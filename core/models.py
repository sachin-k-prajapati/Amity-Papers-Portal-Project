from django.db import models
from django.utils.text import slugify
from cloudinary_storage.storage import MediaCloudinaryStorage, RawMediaCloudinaryStorage

class Institute(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=20, blank=True, null=True, help_text="Short form (e.g., ASET, ALS, etc.)")
    slug = models.SlugField(unique=True, blank=True)

    icon = models.ImageField(upload_to='institutes/', blank=True, null=True, storage=MediaCloudinaryStorage())
    is_active = models.BooleanField(default=True, help_text="Is this institute currently active?")
    is_featured = models.BooleanField(default=False, help_text="Is this institute featured on the homepage?")
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)  # Auto-generate slug if not provided
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.abbreviation} - {self.name}" if self.abbreviation else self.name


class Program(models.Model):
    institute = models.ForeignKey(Institute, on_delete=models.CASCADE, related_name='programs')
    name = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} ({self.institute.abbreviation})" if self.institute.abbreviation else self.name


class Semester(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='semesters')
    number = models.PositiveSmallIntegerField()
    
    class Meta:
        unique_together = ('program', 'number')
        ordering = ['number']

    def __str__(self):
        return f"Semester {self.number} - {self.program}"


class Subject(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    semesters = models.ManyToManyField(Semester, through='SubjectOffering')
    
    class Meta:
        unique_together = ('code', 'name')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class SubjectOffering(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='offerings')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subject_offerings')

    def __str__(self):
        return f"{self.subject} offered in {self.semester}"


class ExamPaper(models.Model):
    PAPER_TYPES = (
        ('E', 'End Sem'), 
        ('B', 'Back Paper'),
    )

    subject_offering = models.ForeignKey(SubjectOffering, on_delete=models.CASCADE, related_name='papers')
    paper_type = models.CharField(max_length=1, choices=PAPER_TYPES, default='E')
    year = models.PositiveIntegerField()
    file = models.FileField(upload_to='papers/', storage=RawMediaCloudinaryStorage(), max_length=200)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # efficiency field
    title = models.CharField(max_length=300, blank=True, help_text="Auto-generated from filename if empty")
    
    # Denormalized fields for faster queries (reduce joins)
    institute_name = models.CharField(max_length=200, blank=True, editable=False)
    program_name = models.CharField(max_length=200, blank=True, editable=False)
    semester_number = models.PositiveSmallIntegerField(blank=True, null=True, editable=False)
    subject_code = models.CharField(max_length=20, blank=True, editable=False)
    subject_name = models.CharField(max_length=200, blank=True, editable=False)

    class Meta:
        ordering = ['-year', '-uploaded_at']
        indexes = [
            models.Index(fields=['year', 'paper_type']),
            models.Index(fields=['subject_code', 'year']),
            models.Index(fields=['institute_name', 'year']),
        ]

    def save(self, *args, **kwargs):
        # Auto-populate denormalized fields
        if self.subject_offering:
            self.institute_name = self.subject_offering.semester.program.institute.name
            self.program_name = self.subject_offering.semester.program.name
            self.semester_number = self.subject_offering.semester.number
            self.subject_code = self.subject_offering.subject.code
            self.subject_name = self.subject_offering.subject.name
        
        # Only auto-generate filename for new files to prevent breaking existing links
        if self.file and not self.pk and self.subject_offering:  # Only for new records
            # Get original extension
            original_name = self.file.name
            file_extension = original_name.split('.')[-1] if '.' in original_name else 'pdf'
            
            # Create standardized filename components
            subject_code = self.subject_offering.subject.code
            program_name = self.subject_offering.semester.program.name.replace(' ', '_')
            paper_type_name = 'End_Sem' if self.paper_type == 'E' else 'Back_Paper'

            # Format: SUBJECTCODE_YEAR_PAPERTYPE_PROGRAM.extension
            new_filename = f"{subject_code}_{self.year}_{paper_type_name}_{program_name}.{file_extension}"
            self.file.name = new_filename
        
        # Auto-generate title if not provided
        if not self.title and self.subject_offering:
            paper_type_display = 'End Sem' if self.paper_type == 'E' else 'Back Paper'
            self.title = f"{self.subject_offering.subject.code} - {self.subject_offering.subject.name}"
             
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject_code} {self.get_paper_type_display()} ({self.year})"