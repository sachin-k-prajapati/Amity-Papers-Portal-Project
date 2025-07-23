from .models import ExamPaper

def serialize_paper(paper):
    """Convert ExamPaper instance to dictionary for JSON serialization"""
    return {
        'id': paper.id,
        'year': paper.year,
        'paper_type': paper.get_paper_type_display(),
        'institute': paper.subject_offering.semester.program.institute.name,
        'program': paper.subject_offering.semester.program.name,
        'semester': paper.subject_offering.semester.number,
        'subject': paper.subject_offering.subject.name,
        'subject_code': paper.subject_offering.subject.code,
        'url': paper.file.url if paper.file else None
    }

def serialize_papers(papers):
    """Convert queryset or list of ExamPaper instances to list of dictionaries"""
    return [serialize_paper(paper) for paper in papers]

# Legacy class for backward compatibility
class PaperSerializer:
    """Legacy compatibility class - replaced with function-based serialization"""
    def __init__(self, papers, many=False):
        self.papers = papers
        self.many = many
    
    @property
    def data(self):
        if self.many:
            return serialize_papers(self.papers)
        else:
            return serialize_paper(self.papers)