from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView
from django.views import View
from django.db.models import Count, Q
from django.http import JsonResponse, FileResponse, Http404
from .models import Institute, Program, Semester, Subject, SubjectOffering, ExamPaper
from .serializers import serialize_papers
from django.core.exceptions import ValidationError
from django.utils.html import escape
import re
import json
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods

class HomeView(ListView):
    template_name = 'core/home.html'
    model = Institute
    context_object_name = 'institutes'

    def get_queryset(self):
        return Institute.objects.filter(is_active=True).annotate(
            paper_count=Count('programs__semesters__subject_offerings__papers', distinct=True)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['featured_institutes'] = self.get_queryset().filter(is_featured=True)[:3]
        context['recent_papers'] = ExamPaper.objects.select_related(
            'subject_offering__subject',
            'subject_offering__semester__program__institute',
        ).order_by('-uploaded_at')[:9]

        # Fetch all programs for ASET (Amity School of Engineering & Technology)
        aset_institute = Institute.objects.filter(slug='amity-school-of-engineering-technology').first()
        if aset_institute:
            context['aset_programs'] = aset_institute.programs.all()
            
        # Total Counts
        context['total_institutes'] = Institute.objects.filter(is_active=True).count()
        context['total_papers'] = ExamPaper.objects.count()
        context['total_subjects'] = Subject.objects.count()

        return context

class PaperListView(ListView):
    model = ExamPaper
    template_name = 'core/papers.html'
    paginate_by = 12
    context_object_name = 'papers'

    def get_queryset(self):
        queryset = ExamPaper.objects.all().select_related(
            'subject_offering',
            'subject_offering__subject',
            'subject_offering__semester',
            'subject_offering__semester__program',
            'subject_offering__semester__program__institute'
        )

        # Apply filters
        if institute_slug := self.request.GET.get('institute'):
            queryset = queryset.filter(
                subject_offering__subject__semester__program__institute__slug=institute_slug
            )

        if program_id := self.request.GET.get('program'):
            queryset = queryset.filter(
                subject_offering__subject__semester__program_id=program_id
            )

        if semester_id := self.request.GET.get('semester'):
            queryset = queryset.filter(
                subject_offering__subject__semester_id=semester_id
            )

        if years := self.request.GET.getlist('year'):
            queryset = queryset.filter(year__in=years)

        if subjects := self.request.GET.getlist('subject'):
            queryset = queryset.filter(subject_offering__subject_id__in=subjects)

        # Sorting
        sort_by = self.request.GET.get('sort', 'recent')
        if sort_by == 'alphabetical':
            queryset = queryset.order_by('subject_offering__subject__name')
        else:  # Default to recent
            queryset = queryset.order_by('-year', '-uploaded_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['institutes'] = Institute.objects.all()
        
        # Preserve filter state
        context['selected_institute'] = self.request.GET.get('institute')
        context['selected_program'] = self.request.GET.get('program')
        context['selected_semester'] = self.request.GET.get('semester')
        context['selected_years'] = list(map(int, self.request.GET.getlist('year', [])))
        context['selected_subjects'] = list(map(int, self.request.GET.getlist('subject', [])))
        context['sort_by'] = self.request.GET.get('sort', 'recent')
        
        return context

class FilterPapersView(View):
    def get(self, request, *args, **kwargs):
        
        queryset = ExamPaper.objects.all().select_related(
            'subject_offering',
            'subject_offering__subject',
            'subject_offering__semester',
            'subject_offering__semester__program',
            'subject_offering__semester__program__institute'
        )
        
        initial_count = queryset.count()
        
        # Get available years and subjects for filtering with proper ordering
        all_years = sorted(
            list(queryset.values_list('year', flat=True).distinct()), 
            reverse=True
        )
        
        # Get distinct subjects by code with proper ordering
        subject_data = queryset.values(
            'subject_offering__subject_id',
            'subject_offering__subject__code',
            'subject_offering__subject__name'
        ).distinct().order_by('subject_offering__subject__code')
        
        all_subjects = [(item['subject_offering__subject_id'], 
                        f"{item['subject_offering__subject__code']} - {item['subject_offering__subject__name']}")
                       for item in subject_data]

        # Apply filters
        if institute_slug := request.GET.get('institute'):
            queryset = queryset.filter(
                subject_offering__semester__program__institute__slug=institute_slug
            )

        if program_id := request.GET.get('program'):
            queryset = queryset.filter(
                subject_offering__semester__program_id=program_id
            )

        if semester_id := request.GET.get('semester'):
            queryset = queryset.filter(
                subject_offering__semester_id=semester_id
            )

        # Apply year filter - simple intersection
        years = request.GET.getlist('year')
        if years:
            # Filter out empty values and convert to integers
            year_list = []
            for year in years:
                if year and year.strip():
                    try:
                        year_list.append(int(year))
                    except ValueError:
                        continue
            
            if year_list:
                queryset = queryset.filter(year__in=year_list)

        # Apply subject filter - simple intersection
        subjects = request.GET.getlist('subject')
        if subjects:
            # Filter out empty values and convert to integers
            subject_list = []
            for subject in subjects:
                if subject and subject.strip():
                    try:
                        subject_list.append(int(subject))
                    except ValueError:
                        continue
            
            if subject_list:
                queryset = queryset.filter(subject_offering__subject_id__in=subject_list)

        # Count before sorting
        final_count = queryset.count()

        # Sorting logic
        sort_by = request.GET.get('sort', 'recent')
        if sort_by == 'alphabetical':
            queryset = queryset.order_by('subject_offering__subject__name')
        else:  # Default to recent
            queryset = queryset.order_by('-year', '-uploaded_at')

        papers = serialize_papers(queryset)
        return JsonResponse({'papers': papers})

@cache_page(60 * 10)  # Cache for 10 minutes
@require_http_methods(["GET"])
def api_programs(request):
    institute_slug = request.GET.get('institute')
    
    if not institute_slug:
        return JsonResponse([], safe=False)
    
    # Validate slug format
    if not re.match(r'^[\w-]+$', institute_slug):
        return JsonResponse({'error': 'Invalid institute slug'}, status=400)
    
    try:
        programs = Program.objects.filter(
            institute__slug=institute_slug
        ).values('id', 'name').order_by('name')
        return JsonResponse(list(programs), safe=False)
    except Exception as e:
        return JsonResponse({'error': 'Failed to fetch programs'}, status=500)

@cache_page(60 * 10)  # Cache for 10 minutes  
@require_http_methods(["GET"])
def api_semesters(request):
    program_id = request.GET.get('program')
    
    if not program_id:
        return JsonResponse([], safe=False)
    
    # Validate program_id is integer
    try:
        program_id = int(program_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid program ID'}, status=400)
    
    try:
        semesters = Semester.objects.filter(
            program_id=program_id
        ).values('id', 'number').order_by('number')
        return JsonResponse(list(semesters), safe=False)
    except Exception as e:
        return JsonResponse({'error': 'Failed to fetch semesters'}, status=500)

@cache_page(60 * 10)  # Cache for 10 minutes
@require_http_methods(["GET"])
def api_subjects(request):
    semester_id = request.GET.get('semester')

    if not semester_id:
        return JsonResponse({'subjects': [], 'years': []}, safe=False)

    # Validate semester_id is integer
    try:
        semester_id = int(semester_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid semester ID'}, status=400)

    try:
        # Get all papers for this semester
        papers = ExamPaper.objects.filter(
            subject_offering__semester_id=semester_id
        ).select_related(
            'subject_offering__subject'
        ).values(
            'subject_offering__subject__id',
            'subject_offering__subject__code', 
            'subject_offering__subject__name',
            'year'
        )
        
        # Group subjects by code to get distinct subjects
        subjects_dict = {}
        all_years = set()
        
        for paper in papers:
            subject_id = paper['subject_offering__subject__id']
            subject_code = paper['subject_offering__subject__code']
            subject_name = paper['subject_offering__subject__name']
            year = paper['year']
            
            all_years.add(year)
            
            # Use subject_code as key to ensure uniqueness by code
            if subject_code not in subjects_dict:
                subjects_dict[subject_code] = {
                    'id': subject_id,
                    'code': subject_code,
                    'name': subject_name,
                    'years': set()
                }
            
            subjects_dict[subject_code]['years'].add(year)
        
        # Convert to final format with ordered data
        subjects_list = []
        for code, subject_data in sorted(subjects_dict.items()):  # Sort by subject code
            subjects_list.append({
                'id': subject_data['id'],
                'code': subject_data['code'],
                'name': subject_data['name'],
                'years': sorted(list(subject_data['years']), reverse=True)  # Years in descending order
            })
        
        # Get distinct years in descending order
        years_list = sorted(list(all_years), reverse=True)
        
        return JsonResponse({
            'subjects': subjects_list,
            'years': years_list
        }, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': 'Failed to fetch subjects'}, status=500)

@cache_page(60 * 5)  # Cache for 5 minutes
@require_http_methods(["GET"])
def api_search(request):
    query = request.GET.get('q', '').strip()
    
    # Input validation
    if not query:
        return JsonResponse([], safe=False)
    
    if len(query) > 100:  # Limit query length
        return JsonResponse({'error': 'Query too long'}, status=400)
    
    # Sanitize input
    query = escape(query)
    
    try:
        # If query matches a subject code pattern like "CS301" or "MA104"
        code_pattern = r'^[A-Za-z]{2,4}\d{3,4}$'

        if re.match(code_pattern, query):
            # Prioritize exact match on subject code
            papers = ExamPaper.objects.filter(
                subject_offering__subject__code__iexact=query,
            ).select_related(
                'subject_offering__subject',
                'subject_offering__semester__program__institute'
            )
        else:
            # General full-text search
            papers = ExamPaper.objects.filter(
                Q(subject_offering__subject__name__icontains=query) |
                Q(subject_offering__subject__code__icontains=query),
            ).select_related(
                'subject_offering__subject',
                'subject_offering__semester__program__institute'
            )
        
        # Limit results for better performance
        papers = papers[:10]
        
        papers_data = serialize_papers(papers)
        return JsonResponse(papers_data, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': 'Search failed'}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_generateReport(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    
    # Validate required fields
    institute_slug = data.get('institute')
    if not institute_slug:
        return JsonResponse({'error': 'Institute is required'}, status=400)
    
    program = data.get('program')
    semester = data.get('semester')
    years = data.get('years', [])
    subjects = data.get('subjects', [])
    
    # Validate data types
    if not isinstance(years, list) or not isinstance(subjects, list):
        return JsonResponse({'error': 'Years and subjects must be arrays'}, status=400)
    
    # Validate numeric values
    try:
        if program:
            program = int(program)
        if semester:
            semester = int(semester)
        years = [int(y) for y in years if y]
        subjects = [int(s) for s in subjects if s]
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid numeric values'}, status=400)

    try:
        # fetching the paper based on the filters
        queryset = ExamPaper.objects.filter(
            subject_offering__semester__program__institute__slug=institute_slug
        ).select_related(
            'subject_offering',
            'subject_offering__subject',
            'subject_offering__semester',
            'subject_offering__semester__program',
            'subject_offering__semester__program__institute'
        )
        
        if institute_slug:
            queryset = queryset.filter(subject_offering__semester__program__institute__slug=institute_slug)

        if program:
            queryset = queryset.filter(subject_offering__semester__program_id=program)
        
        if semester:
            queryset = queryset.filter(subject_offering__semester_id=semester)
        
        if years:
            queryset = queryset.filter(year__in=years)

        if subjects:
            queryset = queryset.filter(subject_offering__subject_id__in=subjects)
            
        # Final count
        final_count = queryset.count()

        papers_data = serialize_papers(queryset)
        return JsonResponse({'success': True, 'papers': papers_data})
        
    except Exception as e:
        return JsonResponse({'error': 'Failed to generate report'}, status=500)

@csrf_exempt
def api_report(request):
    return render(request, 'core/report.html')

@require_http_methods(["GET"])
def preview_paper(request, paper_id):
    try:
        # Validate paper_id is integer
        paper_id = int(paper_id)
    except (ValueError, TypeError):
        raise Http404("Invalid paper ID")
    
    paper = get_object_or_404(ExamPaper, id=paper_id)
    
    try:
        if not paper.file:
            raise Http404("File not found")
        
        # For Cloudinary files, we can directly serve the URL
        # Cloudinary URLs are publicly accessible and work great in iframes
        file_url = paper.file.url
        
        # If it's a Cloudinary URL, redirect to it
        if 'cloudinary.com' in file_url:
            from django.http import HttpResponseRedirect
            return HttpResponseRedirect(file_url)
        
        # For local files (fallback), serve via FileResponse
        file_path = paper.file.path
        
        # Security check - ensure file exists and is accessible
        import os
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            # Log the broken file but don't expose internal paths
            print(f"Warning: Paper {paper_id} has broken file link: {paper.file.name}")
            raise Http404("File not available - please contact administrator")
        
        return FileResponse(
            open(file_path, 'rb'), 
            content_type='application/pdf',
            as_attachment=False,
            filename=f"{paper.subject_offering.subject.code}_{paper.year}.pdf"
        )
    except Exception as e:
        raise Http404("File not available")

@require_http_methods(["GET"])
def download_paper(request, paper_id):
    try:
        # Validate paper_id is integer
        paper_id = int(paper_id)
    except (ValueError, TypeError):
        raise Http404("Invalid paper ID")
    
    paper = get_object_or_404(ExamPaper, id=paper_id)
    
    try:
        if not paper.file:
            raise Http404("File not found")
        
        # For Cloudinary files, we need to serve them through Django to force download
        file_url = paper.file.url
        
        if 'cloudinary.com' in file_url:
            # For Cloudinary files, fetch and serve with download headers
            import requests
            from django.http import HttpResponse
            
            response = requests.get(file_url)
            if response.status_code == 200:
                # Generate filename 
                subject_code = paper.subject_offering.subject.code
                subject_name = paper.subject_offering.subject.name.replace(' ', '_')
                paper_type = 'End_Sem' if paper.paper_type == 'E' else 'Back_Paper'
                program_name = paper.subject_offering.semester.program.name.replace(' ', '_').replace('.', '')
                filename = f"{subject_code}_{subject_name}_{paper.year}_{paper_type}_{program_name}.pdf"
                
                http_response = HttpResponse(
                    response.content,
                    content_type='application/pdf'
                )
                http_response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return http_response
            else:
                raise Http404("File not available from storage")
        
        # For local files (fallback), serve via FileResponse
        file_path = paper.file.path
        
        # Security check - ensure file exists and is accessible
        import os
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            # Log the broken file but don't expose internal paths
            print(f"Warning: Paper {paper_id} has broken file link: {paper.file.name}")
            raise Http404("File not available - please contact administrator")
        
        return FileResponse(
            open(file_path, 'rb'), 
            content_type='application/pdf',
            as_attachment=True,  # This forces download
            filename=f"{paper.subject_offering.subject.code}_{paper.year}.pdf"
        )
    except Exception as e:
        raise Http404("File not available")
