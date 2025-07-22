"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views
from core.views import preview_paper, FilterPapersView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.HomeView.as_view(), name='home'),
    path('papers/', views.PaperListView.as_view(), name='paper_list'),
    
    # API Endpoints
    path('api/programs/', views.api_programs, name='api_programs'),
    path('api/semesters/', views.api_semesters, name='api_semesters'),
    path('api/search/', views.api_search, name='api_search'),
    path("api/subjects/", views.api_subjects, name="api_subjects"),
    
    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
    path('papers/preview/<int:paper_id>/', preview_paper, name='preview_paper'),
    
    # Filter papers
    path('api/filter-papers/', FilterPapersView.as_view(), name='filter-papers'),
    path('api/generate-report/', views.api_generateReport, name='api_generateReport'),
    path('report.html/', views.api_report, name='api_report'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)