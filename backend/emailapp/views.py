from django.shortcuts import render
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from .models import EmailAccount, EmailMessage, EmailAttachment, EmailFile, EmailClassificationRule
from .serializers import (
    EmailAccountSerializer,
    EmailMessageSerializer,
    EmailAttachmentSerializer,
    EmailFileSerializer,
    EmailClassificationRuleSerializer
)
from .services import EmailFetchService, EmailProcessingService
import logging
import os

logger = logging.getLogger(__name__)

class EmailAccountViewSet(viewsets.ModelViewSet):
    queryset = EmailAccount.objects.all()
    serializer_class = EmailAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmailAccount.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class EmailMessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmailMessage.objects.all()
    serializer_class = EmailMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmailMessage.objects.filter(account__user=self.request.user)

class EmailAttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EmailAttachment.objects.all()
    serializer_class = EmailAttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmailAttachment.objects.filter(email__account__user=self.request.user)

class EmailFileViewSet(viewsets.ModelViewSet):
    queryset = EmailFile.objects.all()
    serializer_class = EmailFileSerializer
    permission_classes = [permissions.IsAuthenticated]
    email_service = EmailProcessingService()

    def get_queryset(self):
        return EmailFile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        logger.info(f"Received file upload request: {self.request.FILES}")
        try:
            file_obj = self.request.FILES['file']
            file_type = os.path.splitext(file_obj.name)[1].lower()[1:]
            if file_type not in dict(EmailFile.FILE_TYPE_CHOICES):
                file_type = 'other'

            instance = serializer.save(
                user=self.request.user,
                file=file_obj,
                file_name=file_obj.name,
                file_type=file_type,
                size=file_obj.size
            )
            # 处理文件
            self.email_service.process_email_file(instance)
            instance.save()
        except Exception as e:
            logger.error(f"Error processing file upload: {str(e)}")
            raise

class EmailClassificationRuleViewSet(viewsets.ModelViewSet):
    queryset = EmailClassificationRule.objects.all()
    serializer_class = EmailClassificationRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return EmailClassificationRule.objects.all()

    @action(detail=False, methods=['post'])
    def test_rule(self, request):
        """Test a rule against sample email data"""
        rule_data = request.data.get('rule')
        email_data = request.data.get('email')
        
        if not rule_data or not email_data:
            return Response(
                {'error': 'Both rule and email data are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 创建临时规则对象
        rule = EmailClassificationRule(**rule_data)
        
        # 模拟邮件对象
        class MockEmail:
            def __init__(self, data):
                self.subject = data.get('subject', '')
                self.sender = data.get('from', '')
                self.body_text = data.get('body', '')
                self.attachment_count = len(data.get('attachments', []))
                self.total_attachment_size = sum(
                    a.get('size', 0) for a in data.get('attachments', [])
                )
        
        mock_email = MockEmail(email_data)
        
        # 测试规则匹配
        matches = True
        reasons = []
        
        # 检查发件人域名
        if rule.sender_domains:
            sender_domain = mock_email.sender.split('@')[-1].lower()
            if sender_domain not in rule.sender_domains:
                matches = False
                reasons.append('Sender domain does not match')
        
        # 检查主题关键词
        if rule.subject_keywords and not any(
            kw.lower() in mock_email.subject.lower() 
            for kw in rule.subject_keywords
        ):
            matches = False
            reasons.append('Subject keywords not found')
        
        # 检查正文关键词
        if rule.body_keywords and not any(
            kw.lower() in mock_email.body_text.lower() 
            for kw in rule.body_keywords
        ):
            matches = False
            reasons.append('Body keywords not found')
        
        # 检查附件数量
        if mock_email.attachment_count < rule.min_attachments:
            matches = False
            reasons.append('Too few attachments')
        if rule.max_attachments and mock_email.attachment_count > rule.max_attachments:
            matches = False
            reasons.append('Too many attachments')
        
        # 检查附件大小
        if mock_email.total_attachment_size < rule.min_attachment_size:
            matches = False
            reasons.append('Attachment size too small')
        if rule.max_attachment_size and mock_email.total_attachment_size > rule.max_attachment_size:
            matches = False
            reasons.append('Attachment size too large')
        
        return Response({
            'matches': matches,
            'reasons': reasons if not matches else ['All conditions met'],
            'classification': rule.classification if matches else None
        })

class EmailContentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    email_service = EmailProcessingService()

    def create(self, request):
        """Handle POST request for email content processing"""
        try:
            # 获取请求数据
            data = request.data
            if isinstance(data, str):
                # 如果是字符串，直接作为内容处理
                email_content = {
                    'subject': '',
                    'body': data
                }
            else:
                # 如果是JSON对象，提取subject和body
                email_content = {
                    'subject': data.get('subject', ''),
                    'body': data.get('body', '')
                }
            
            if not email_content['subject'] and not email_content['body']:
                return Response(
                    {'error': 'Email content cannot be empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 构造邮件内容字符串
            content = f"Subject: {email_content['subject']}\n\nBody: {email_content['body']}"
            
            # 处理内容
            result = self.email_service.process_email_content(content)
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error processing email content: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def classify(self, request):
        """Classify email content"""
        try:
            data = request.data
            if isinstance(data, str):
                email_content = {
                    'subject': '',
                    'body': data
                }
            else:
                email_content = {
                    'subject': data.get('subject', ''),
                    'body': data.get('body', '')
                }
            
            if not email_content['subject'] and not email_content['body']:
                return Response(
                    {'error': 'Email content cannot be empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            content = f"Subject: {email_content['subject']}\n\nBody: {email_content['body']}"
            result = self.email_service.process_email_content(content)
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error classifying email content: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
