from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from classifier.models import ClassificationResult
from emailapp.models import EmailMessage
from fileapp.models import ProcessedFile, TextInput

class UserRegistrationView(generics.CreateAPIView):
    """View for user registration"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not all([username, email, password]):
            return Response(
                {'error': 'Please provide username, email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            return Response(
                {'message': 'User created successfully'},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class UserProfileView(generics.RetrieveUpdateAPIView):
    """View for retrieving and updating user profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({
            'username': user.username,
            'email': user.email,
            'date_joined': user.date_joined
        })
    
    def put(self, request, *args, **kwargs):
        user = request.user
        email = request.data.get('email')
        
        if email:
            user.email = email
            user.save()
            
        return Response({
            'message': 'Profile updated successfully'
        })

class DashboardView(APIView):
    """View for dashboard statistics and recent activities"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        last_week = timezone.now() - timedelta(days=7)
        
        # Get recent statistics
        recent_classifications = ClassificationResult.objects.filter(
            user=user,
            created_at__gte=last_week
        ).count()
        
        recent_emails = EmailMessage.objects.filter(
            account__user=user,
            created_at__gte=last_week
        ).count()
        
        recent_files = ProcessedFile.objects.filter(
            user=user,
            created_at__gte=last_week
        ).count()
        
        recent_texts = TextInput.objects.filter(
            user=user,
            created_at__gte=last_week
        ).count()
        
        # Get classification distribution
        classification_stats = ClassificationResult.objects.filter(
            user=user
        ).values('classification').annotate(
            count=Count('classification')
        ).order_by('-count')[:5]
        
        return Response({
            'recent_stats': {
                'classifications': recent_classifications,
                'emails': recent_emails,
                'files': recent_files,
                'texts': recent_texts
            },
            'classification_distribution': classification_stats
        })

class StatsView(APIView):
    """View for detailed statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        time_period = request.query_params.get('period', 'week')
        
        if time_period == 'week':
            start_date = timezone.now() - timedelta(days=7)
        elif time_period == 'month':
            start_date = timezone.now() - timedelta(days=30)
        else:
            start_date = timezone.now() - timedelta(days=365)
            
        # Get statistics for the period
        stats = {
            'classifications': ClassificationResult.objects.filter(
                user=user,
                created_at__gte=start_date
            ).count(),
            'emails': EmailMessage.objects.filter(
                account__user=user,
                created_at__gte=start_date
            ).count(),
            'files': ProcessedFile.objects.filter(
                user=user,
                created_at__gte=start_date
            ).count(),
            'texts': TextInput.objects.filter(
                user=user,
                created_at__gte=start_date
            ).count()
        }
        
        return Response(stats)
