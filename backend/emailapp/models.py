from django.db import models
from django.contrib.auth.models import User
from classifier.models import ClassificationResult

class EmailAccount(models.Model):
    """Model for storing email account configurations"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField()
    server_type = models.CharField(max_length=10, choices=[('imap', 'IMAP'), ('pop3', 'POP3')])
    server_host = models.CharField(max_length=255)
    server_port = models.IntegerField()
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)  # Should be encrypted in production
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

class EmailMessage(models.Model):
    """Model for storing processed emails"""
    account = models.ForeignKey(EmailAccount, on_delete=models.CASCADE)
    message_id = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=1000)
    sender = models.EmailField()
    recipients = models.JSONField()
    content = models.TextField()
    attachments = models.JSONField(default=list)
    received_date = models.DateTimeField()
    processed = models.BooleanField(default=False)
    classification_result = models.ForeignKey('classifier.ClassificationResult', 
                                            on_delete=models.SET_NULL, 
                                            null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject

class EmailAttachment(models.Model):
    """Model for storing email attachments"""
    email = models.ForeignKey(EmailMessage, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.IntegerField()
    file = models.FileField(upload_to='email_attachments/')
    processed = models.BooleanField(default=False)
    classification_result = models.ForeignKey('classifier.ClassificationResult', 
                                            on_delete=models.SET_NULL, 
                                            null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name

class EmailFile(models.Model):
    """Model for storing processed email files"""
    FILE_TYPE_CHOICES = [
        ('txt', 'Text File'),
        ('html', 'HTML File'),
        ('eml', 'EML File'),
        ('oft', 'OFT File'),
        ('msg', 'MSG File'),
        ('other', 'Other'),
    ]

    CLASSIFICATION_LEVEL_CHOICES = [
        ('rule', 'Rule Engine'),
        ('fasttext', 'FastText Model'),
        ('bert', 'BERT Model'),
        ('llm', 'LLM Model'),
        ('unknown', 'Unknown'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='email_files/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    size = models.BigIntegerField(default=0)
    processed = models.BooleanField(default=False)
    
    # 存储邮件内容
    email_content = models.JSONField(null=True, blank=True)
    
    # 存储分类结果
    classification_result = models.JSONField(null=True, blank=True)
    classification_level = models.CharField(
        max_length=20, 
        choices=CLASSIFICATION_LEVEL_CHOICES,
        default='unknown'
    )
    confidence_score = models.FloatField(default=0.0)
    processing_time = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return str(self.file_name)

class EmailClassificationRule(models.Model):
    """Model for storing email classification rules"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Rule conditions
    sender_domains = models.JSONField(default=list)  # 存储为 JSON 数组
    subject_keywords = models.JSONField(default=list)  # 存储为 JSON 数组
    body_keywords = models.JSONField(default=list)  # 存储为 JSON 数组
    min_attachments = models.IntegerField(default=0)
    max_attachments = models.IntegerField(null=True, blank=True)
    min_attachment_size = models.BigIntegerField(default=0)
    max_attachment_size = models.BigIntegerField(null=True, blank=True)
    
    # Classification result
    classification = models.CharField(max_length=100)
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority']

    def __str__(self) -> str:
        return str(self.name)
