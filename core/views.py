from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse, FileResponse
from .models import Institute, Program, Semester, Subject, SubjectOffering, ExamPaper
from .serializers import PaperSerializer
import re
import json
from django.views.decorators.csrf import csrf_exempt

class HomeView(ListView):
    template_name = 'core/home.html'
    model = Institute
    context_object_name = 'institutes'

    def get_queryset(self):
        return Institute.objects.filter(is_active=True).annotate(
            paper_count=Count('programs__semesters__subject_offerings__exam_papers', distinct=True)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['featured_institutes'] = self.get_queryset().filter(is_featured=True)[:3]
        context['recent_papers'] = ExamPaper.objects.select_related(
            'subject_offering__subject',
            'subject_offering__semester__program__institute',
        ).order_by('-uploaded_at')[:6]

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
    paginate_by = 3
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

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request - return JSON
            papers_data = {
                'papers': [{
                    'id': paper.id,
                    'title': paper.title,
                    # Add other fields you need
                } for paper in context['papers']],
                'paginator': {
                    'num_pages': context['papers'].paginator.num_pages,
                    'count': context['papers'].paginator.count,
                }
            }
            return JsonResponse(papers_data)
        else:
            # Normal request - return HTML
            return super().render_to_response(context, **response_kwargs)

class FilterPapersView(View):
    def get(self, request, *args, **kwargs):
        # Debug: Print the received parameters
        print("=" * 50)
        print("FILTER REQUEST DEBUG:")
        print("Received GET parameters:", dict(request.GET))
        
        queryset = ExamPaper.objects.all().select_related(
            'subject_offering',
            'subject_offering__subject',
            'subject_offering__semester',
            'subject_offering__semester__program',
            'subject_offering__semester__program__institute'
        )
        
        initial_count = queryset.count()
        print(f"Initial paper count: {initial_count}")
        
        # Debug: Show available years and subjects
        all_years = queryset.values_list('year', flat=True).distinct()
        all_subjects = queryset.values_list('subject_offering__subject_id', 'subject_offering__subject__name').distinct()
        print(f"Available years in database: {list(all_years)}")
        print(f"Available subjects in database: {list(all_subjects)[:5]}...")  # Show first 5

        # Apply filters
        if institute_slug := request.GET.get('institute'):
            queryset = queryset.filter(
                subject_offering__semester__program__institute__slug=institute_slug
            )
            print(f"After institute filter: {queryset.count()} papers")

        if program_id := request.GET.get('program'):
            queryset = queryset.filter(
                subject_offering__semester__program_id=program_id
            )
            print(f"After program filter: {queryset.count()} papers")

        if semester_id := request.GET.get('semester'):
            queryset = queryset.filter(
                subject_offering__semester_id=semester_id
            )
            print(f"After semester filter: {queryset.count()} papers")

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
                print(f"After year filter: {queryset.count()} papers (filtered by: {year_list})")

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
                print(f"After subject filter: {queryset.count()} papers (filtered by: {subject_list})")

        # Count before sorting
        final_count = queryset.count()
        print(f"Final paper count before sorting: {final_count}")
        print("=" * 50)

        # Sorting logic
        sort_by = request.GET.get('sort', 'recent')
        if sort_by == 'alphabetical':
            queryset = queryset.order_by('subject_offering__subject__name')
        else:  # Default to recent
            queryset = queryset.order_by('-year', '-uploaded_at')

        papers = PaperSerializer(queryset, many=True).data
        return JsonResponse({'papers': papers})

def api_programs(request):
    institute_slug = request.GET.get('institute')
    programs = Program.objects.filter(
        institute__slug=institute_slug
    ).values('id', 'name')
    return JsonResponse(list(programs), safe=False)

def api_semesters(request):
    program_id = request.GET.get('program')
    semesters = Semester.objects.filter(
        program_id=program_id
    ).values('id', 'number')
    return JsonResponse(list(semesters), safe=False)

def api_subjects(request):
    semester_id = request.GET.get('semester')

    if not semester_id:
        return JsonResponse([], safe=False)

    offerings = SubjectOffering.objects.filter(
        semester_id=semester_id,
        exam_papers__isnull=False  # Only include those with papers
    ).select_related('subject').prefetch_related('exam_papers').distinct()

    response_data = []
    # Collect unique subjects and their years
    seen = set()
    for offering in offerings:
        years = offering.exam_papers.values_list('year', flat=True).distinct()
        for year in years:
            if (offering.subject.id, year) not in seen:
                seen.add((offering.subject.id, year))
                response_data.append({
                    "id": offering.subject.id,
                    "name": offering.subject.name,
                    "code": offering.subject.code,
                    "year": year,
                })

    return JsonResponse(response_data, safe=False)


def api_search(request):
    query = request.GET.get('q', '').strip()
    
    # Debugging: Log the search query
    print(f"Search query received: {query}")
    
    # If query matches a subject code pattern like "CS301" or "MA104"
    code_pattern = r'^[A-Za-z]{2,4}\d{3,4}$'

    if re.match(code_pattern, query):
        # Prioritize exact match on subject code
        papers = ExamPaper.objects.filter(
            subject_offering__subject__code__iexact=query,
        )
    else:
        # General full-text search
        papers = ExamPaper.objects.filter(
            Q(subject_offering__subject__name__icontains=query) |
            Q(subject_offering__subject__code__icontains=query),
        )
    
    # Limit results for better performance
    papers = papers[:10]
    
    # Debugging: Log the number of results
    print(f"Number of results found: {papers.count()}")
    
    serializer = PaperSerializer(papers, many=True)
    return JsonResponse(serializer.data, safe=False)

@csrf_exempt
def api_generateReport(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    
    print("Received data for report generation:", data)
    
    institute_slug = data.get('institute')
    program = data.get('program')
    semester = data.get('semester')
    years = data.get('years', [])
    subjects = data.get('subjects', [])
    
    # Debugging: Log the received parameters
    print(f"Generating report with parameters: institute={institute_slug}, program={program}, semester={semester}, years={years}, subjects={subjects}")

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
        
    print(f"After institute filter: {queryset.count()} papers")

    if program:
        queryset = queryset.filter(subject_offering__semester__program_id=program)

    print(f"After program filter: {queryset.count()} papers")
    
    if semester:
        queryset = queryset.filter(subject_offering__semester_id=semester)

    print(f"After semester filter: {queryset.count()} papers")
    
    if years:
        queryset = queryset.filter(year__in=years)
        
    print(f"After year filter: {queryset.count()} papers (filtered by: {years})")

    if subjects:
        queryset = queryset.filter(subject_offering__subject_id__in=subjects)
        
    print(f"After subject filter: {queryset.count()} papers (filtered by: {subjects})")
        
    # Count before sorting
    initial_count = queryset.count()
    print(f"Initial paper count: {initial_count}")

    papers = PaperSerializer(queryset, many=True)
    return JsonResponse({'success': True, 'papers': papers.data})

@csrf_exempt
def api_report(request):
    return render(request, 'core/report.html')

def preview_paper(request, paper_id):
    paper = get_object_or_404(ExamPaper, id=paper_id)
    file_path = paper.file.path  # 'file' is the field storing the PDF
    return FileResponse(open(file_path, 'rb'), content_type='application/pdf')