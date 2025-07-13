import os
import zipfile
import shutil
import tempfile
import csv

from django.contrib import admin, messages
from django.utils.html import format_html
from django.db.models import Count
from django.core.files import File
from django.shortcuts import render, redirect
from django.http import HttpResponse

from .models import Institute, Program, Semester, Subject, ExamPaper, SubjectOffering

# Utility: handle ZIP upload
def handle_bulk_upload(zip_file, uploader, subject_offering=None):
    extraction_path = tempfile.mkdtemp(prefix='papers_upload_')
    try:
        with zipfile.ZipFile(zip_file) as z:
            z.extractall(extraction_path)

        uploaded_count = 0
        for root, _, files in os.walk(extraction_path):
            for filename in files:
                if filename.lower().endswith('.pdf'):
                    filepath = os.path.join(root, filename)
                    with open(filepath, 'rb') as f:
                        paper = ExamPaper(
                            subject_offering=subject_offering,
                            file=File(f, name=filename),
                            year=2023,  # Default/fallback, or parse from filename
                            paper_type='E',  # Default/fallback
                        )
                        paper.save()
                        uploaded_count += 1
        return uploaded_count
    finally:
        shutil.rmtree(extraction_path, ignore_errors=True)

# =================== ADMIN CONFIGS ===================== #

class ProgramInline(admin.TabularInline):
    model = Program
    extra = 1

@admin.register(Institute)
class InstituteAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'paper_count')
    search_fields = ('name',)
    inlines = [ProgramInline]

    def paper_count(self, obj):
        return ExamPaper.objects.filter(
            subject_offering__semester__program__institute=obj
        ).count()
    paper_count.short_description = 'Total Papers'


class SemesterInline(admin.TabularInline):
    model = Semester
    extra = 1

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'institute')
    list_filter = ('institute',)
    search_fields = ('name',)
    inlines = [SemesterInline]


class SubjectOfferingInline(admin.TabularInline):
    model = SubjectOffering
    extra = 1

@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('number', 'program')
    list_filter = ('program__institute', 'program')
    inlines = [SubjectOfferingInline]


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ['subject_offering', 'paper_type', 'year', 'uploaded_at']
    readonly_fields = ['uploaded_at']
    list_filter = ['paper_type', 'year']

    actions = ['export_as_csv', 'bulk_upload_papers']

    def bulk_upload_papers(self, request, queryset):
        """Bulk upload form for ZIPs"""
        if request.method == 'POST' and 'zip_file' in request.FILES:
            zip_file = request.FILES['zip_file']
            offering_id = request.POST.get('subject_offering')

            try:
                subject_offering = SubjectOffering.objects.get(id=offering_id)
                uploaded_count = handle_bulk_upload(zip_file, request.user, subject_offering)
                self.message_user(request, f'Successfully uploaded {uploaded_count} papers.', level=messages.SUCCESS)
                return redirect('admin:core_exampaper_changelist')
            except Exception as e:
                messages.error(request, f'Upload error: {str(e)}')

        offerings = SubjectOffering.objects.select_related('subject', 'semester__program__institute')
        context = {
            'title': 'Bulk Upload Papers',
            'offerings': offerings,
            'opts': self.model._meta,
        }
        return render(request, 'admin/bulk_upload.html', context)

    bulk_upload_papers.short_description = "Bulk Upload Papers from ZIP"

    def export_as_csv(self, request, queryset):
        """Export ExamPaper data to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="exam_papers.csv"'
        writer = csv.writer(response)
        writer.writerow(['Subject', 'Program', 'Semester', 'Year', 'Type', 'Uploaded At'])
        for paper in queryset:
            writer.writerow([
                paper.subject_offering.subject.name,
                paper.subject_offering.semester.program.name,
                f"Sem {paper.subject_offering.semester.number}",
                paper.year,
                paper.get_paper_type_display(),
                paper.uploaded_at.strftime('%Y-%m-%d'),
            ])
        return response

    export_as_csv.short_description = "Export selected papers as CSV"
