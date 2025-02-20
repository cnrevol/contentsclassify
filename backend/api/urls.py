from django.urls import path
from rest_framework.authtoken import views as auth_views
from . import views

app_name = 'api'

urlpatterns = [
    path('auth/token/', auth_views.obtain_auth_token, name='api-token'),
    path('auth/register/', views.UserRegistrationView.as_view(), name='user-registration'),
    path('auth/profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('stats/', views.StatsView.as_view(), name='stats'),
] 