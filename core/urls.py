from django.urls import path
from . import views
from .views import preview_paper, download_paper, FilterPapersView

app_name = 'core'

urlpatterns = [
    # Main pages
    path('', views.HomeView.as_view(), name='home'),
    path('papers/', views.PaperListView.as_view(), name='paper_list'),
    
    # API Endpoints
    path('api/programs/', views.api_programs, name='api_programs'),
    path('api/semesters/', views.api_semesters, name='api_semesters'),
    path('api/search/', views.api_search, name='api_search'),
    path('api/subjects/', views.api_subjects, name='api_subjects'),
    path('api/filter-papers/', FilterPapersView.as_view(), name='filter_papers'),
    path('api/generate-report/', views.api_generateReport, name='api_generateReport'),
    
    # Paper preview and download
    path('papers/preview/<int:paper_id>/', preview_paper, name='preview_paper'),
    path('papers/download/<int:paper_id>/', download_paper, name='download_paper'),
    
    # Report page
    path('report/', views.api_report, name='report'),

    # Contact and departments
    path('contact/', views.contact_us, name='contact_us'),
    path('departments/', views.departments, name='departments'),
    path('report-issue/', views.report_issue, name='report_issue'),
]
