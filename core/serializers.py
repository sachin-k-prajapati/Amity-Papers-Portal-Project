from rest_framework import serializers
from .models import ExamPaper

class PaperSerializer(serializers.ModelSerializer):
    institute = serializers.CharField(source='subject_offering.semester.program.institute.name')
    program = serializers.CharField(source='subject_offering.semester.program.name')
    semester = serializers.CharField(source='subject_offering.semester.number')
    subject = serializers.CharField(source='subject_offering.subject.name')
    subject_code = serializers.CharField(source='subject_offering.subject.code')
    paper_type = serializers.CharField(source='get_paper_type_display')
    url = serializers.SerializerMethodField()

    class Meta:
        model = ExamPaper
        fields = [
            'id', 'year', 'paper_type', 
            'institute', 'program', 'semester', 
            'subject', 'subject_code', 'url'
        ]

    def get_url(self, obj):
        if obj.file:
            return obj.file.url
        return None