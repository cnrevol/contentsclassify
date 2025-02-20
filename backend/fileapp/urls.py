from django.urls import path
from . import views
from .views import get_llm_providers

app_name = 'fileapp'

urlpatterns = [
    path('upload/', views.FileUploadView.as_view(), name='file-upload'),
    path('files/', views.ProcessedFileListView.as_view(), name='file-list'),
    path('files/<int:pk>/', views.ProcessedFileDetailView.as_view(), name='file-detail'),
    path('llm-providers/', get_llm_providers, name='get_llm_providers'),
    path('text/', views.TextInputListCreateView.as_view(), name='text-list-create'),
    path('text/<int:pk>/', views.TextInputDetailView.as_view(), name='text-detail'),
] 