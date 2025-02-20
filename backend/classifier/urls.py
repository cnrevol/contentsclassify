from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryGroupListCreateView,
    CategoryGroupDetailView,
    CategoryListCreateView,
    ClassificationRuleListCreateView,
    ClassificationRuleDetailView,
    ClassificationResultListView,
    ClassificationResultDetailView,
    ProcessingJobListCreateView,
    ProcessingJobDetailView,
)

app_name = 'classifier'

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'category-groups', CategoryGroupDetailView, basename='category-group')

urlpatterns = [
    # Classification Rules
    path('rules/', ClassificationRuleListCreateView.as_view(), name='rule-list'),
    path('rules/<int:pk>/', ClassificationRuleDetailView.as_view(), name='rule-detail'),
    
    # Classification Results
    path('results/', ClassificationResultListView.as_view(), name='result-list'),
    path('results/<int:pk>/', ClassificationResultDetailView.as_view(), name='result-detail'),
    
    # Processing Jobs
    path('jobs/', ProcessingJobListCreateView.as_view(), name='job-list'),
    path('jobs/<int:pk>/', ProcessingJobDetailView.as_view(), name='job-detail'),
    
    # Categories
    path('category-groups/<int:group_id>/categories/', CategoryListCreateView.as_view(), name='category-list'),
]

# Add router URLs to urlpatterns
urlpatterns += router.urls 