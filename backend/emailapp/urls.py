from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'email-files', views.EmailFileViewSet, basename='email-file')
router.register(r'email-rules', views.EmailClassificationRuleViewSet, basename='email-rule')
router.register(r'messages', views.EmailMessageViewSet, basename='email-message')
router.register(r'accounts', views.EmailAccountViewSet, basename='email-account')
router.register(r'attachments', views.EmailAttachmentViewSet, basename='email-attachment')
router.register(r'content', views.EmailContentViewSet, basename='email-content')

urlpatterns = [
    path('', include(router.urls)),
]