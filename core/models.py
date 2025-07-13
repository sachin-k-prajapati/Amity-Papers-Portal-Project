from django.db import models
from django.utils.text import slugify

class Institute(models.Model):
    name = models.CharField(max_length=200)
    abbreviation = models.CharField(max_length=20, blank=True, null=True, help_text="Short form (e.g., ASET, ALS, etc.)")
    slug = models.SlugField(unique=True, blank=True)

    icon = models.ImageField(upload_to='institutes/', blank=True, null=True)
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

    def __str__(self):
        return f"{self.code} - {self.name}"


class SubjectOffering(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='offerings')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subject_offerings')

    def __str__(self):
        return f"{self.subject} offered in {self.semester}"


class ExamPaper(models.Model):
    PAPER_TYPES = (('E', 'End Sem'), ('B', 'Back Paper'))

    subject_offering = models.ForeignKey(SubjectOffering, on_delete=models.CASCADE, related_name='exam_papers')
    paper_type = models.CharField(max_length=1, choices=PAPER_TYPES)
    year = models.PositiveIntegerField()
    file = models.FileField(upload_to='papers/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject_offering.subject} {self.get_paper_type_display()} Paper ({self.year})"