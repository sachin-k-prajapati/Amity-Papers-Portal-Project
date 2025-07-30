import os
import csv
from django.contrib import admin, messages
from django.core.files import File
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import path
from django.template.response import TemplateResponse

from .models import Institute, Program, Semester, Subject, ExamPaper, SubjectOffering

# =================== ADMIN CONFIGS ===================== #

# Inline to allow managing SubjectOffering within Semester
class SubjectOfferingInline(admin.TabularInline):
    model = SubjectOffering
    extra = 1

# Inline to allow managing Semesters within Program
class SemesterInline(admin.TabularInline):
    model = Semester
    extra = 1

@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'is_active', 'is_featured')
    search_fields = ('name', 'abbreviation')
    list_filter = ('is_active', 'is_featured')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'institute')
    list_filter = ('institute',)
    search_fields = ('name', 'institute__name')
    inlines = [SemesterInline]

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('number', 'program', 'get_institute')
    list_filter = ('program__institute', 'number')
    search_fields = ('program__name', 'program__institute__name')
    inlines = [SubjectOfferingInline]
    autocomplete_fields = ["program"]

    def get_institute(self, obj):
        return obj.program.institute.name
    get_institute.short_description = 'Institute'

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('name', 'code')
    list_filter = ('code',)
 
@admin.register(SubjectOffering)
class SubjectOfferingAdmin(admin.ModelAdmin):
    list_display = ('subject', 'semester')
    list_filter = ('semester__program__institute', 'semester__program', 'semester__number')
    search_fields = ('subject__name', 'subject__code', 'semester__program__name')
    autocomplete_fields = ["subject", "semester"]
    
    def get_program(self, obj):
        return obj.semester.program.name
    get_program.short_description = 'Program'
    
    def get_institute(self, obj):
        return obj.semester.program.institute.name
    get_institute.short_description = 'Institute'

@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject_code', 'institute_name', 'program_name', 'year', 'paper_type']
    list_filter = ['paper_type', 'year', 'institute_name', 'program_name']
    search_fields = ['title', 'subject_code', 'subject_name', 'institute_name']
    readonly_fields = ['uploaded_at', 'institute_name', 'program_name', 'semester_number', 'subject_code', 'subject_name']
    list_per_page = 50
    
    actions = ['export_csv', 'delete_broken_files']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='core_exampaper_bulk_upload'),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        """Simple bulk upload with automatic file name processing"""
        if request.method == 'POST':
            subject_offering_id = request.POST.get('subject_offering')
            files = request.FILES.getlist('files')
            
            if not subject_offering_id:
                messages.error(request, 'Please select a subject offering.')
                return redirect(request.path)
                
            if not files:
                messages.error(request, 'Please select at least one file.')
                return redirect(request.path)
            
            try:
                subject_offering = SubjectOffering.objects.get(id=subject_offering_id)
                success_count = 0
                error_count = 0
                
                for file in files:
                    try:
                        # Extract information from filename
                        filename = file.name.lower()
                        base_name = os.path.splitext(filename)[0]
                        
                        # Extract year (look for 4-digit number)
                        import re
                        year_match = re.search(r'\b(20\d{2})\b', base_name)
                        year = int(year_match.group(1)) if year_match else 2024
                        
                        # Extract paper type from filename
                        paper_type = 'E'  # default End Sem
                        if any(word in base_name for word in ['back', 'backpaper', 'bp', 'compartment', 'reappear']):
                            paper_type = 'B'
                        
                        # Create standardized filename
                        subject_code = subject_offering.subject.code
                        program_name = subject_offering.semester.program.name.replace(' ', '_')
                        paper_type_name = 'End_Sem' if paper_type == 'E' else 'Back_Paper'

                        # Format: SUBJECTCODE_YEAR_PAPERTYPE_PROGRAM.pdf
                        new_filename = f"{subject_code}_{year}_{paper_type_name}_{program_name}.pdf"
                        
                        # Create title for display
                        title = f"{subject_code} - {subject_offering.subject.name}"
                        
                        # Save file with new name
                        file.name = new_filename
                        
                        paper = ExamPaper.objects.create(
                            title=title,
                            subject_offering=subject_offering,
                            year=year,
                            paper_type=paper_type,
                            file=file
                        )
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        messages.error(request, f'Error processing {file.name}: {str(e)}')
                
                if success_count > 0:
                    messages.success(request, f"Successfully uploaded {success_count} papers with auto-detection.")
                
                if error_count > 0:
                    messages.warning(request, f"{error_count} files failed to upload.")
                
                return redirect('admin:core_exampaper_changelist')
                
            except SubjectOffering.DoesNotExist:
                messages.error(request, 'Invalid subject offering selected.')
            except Exception as e:
                messages.error(request, f'Upload failed: {str(e)}')
        
        # Get context for form
        context = {
            'title': 'Bulk Paper Upload',
            'subject_offerings': SubjectOffering.objects.select_related(
                'subject', 'semester__program__institute'
            ).all().order_by('semester__program__institute__name', 'semester__program__name', 'semester__number', 'subject__code'),
            'opts': self.model._meta,
        }
        
        return TemplateResponse(request, 'admin/bulk_upload.html', context)
    
    def delete_broken_files(self, request, queryset):
        """Remove papers with broken file links"""
        import os
        broken_count = 0
        for paper in queryset:
            if paper.file and not os.path.exists(paper.file.path):
                paper.delete()
                broken_count += 1
        
        self.message_user(request, f'{broken_count} papers with broken files deleted.')
    delete_broken_files.short_description = "Delete papers with broken file links"
    
    def export_csv(self, request, queryset):
        """Simple CSV export"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="papers.csv"'
        writer = csv.writer(response)
        writer.writerow(['Title', 'Subject Code', 'Institute', 'Year', 'Paper Type'])
        
        for paper in queryset:
            writer.writerow([
                paper.title,
                paper.subject_code,
                paper.institute_name,
                paper.year,
                paper.get_paper_type_display()
            ])
        return response
    
    export_csv.short_description = "Export selected papers as CSV"
