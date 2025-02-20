from django.db import models
from django.contrib.auth.models import User
from classifier.models import ClassificationResult

class ProcessedFile(models.Model):
    """Model for storing processed files"""
    FILE_TYPE_CHOICES = [
        ('text', 'Text File'),
        ('pdf', 'PDF Document'),
        ('doc', 'Word Document'),
        ('xls', 'Excel Spreadsheet'),
        ('ppt', 'PowerPoint Presentation'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploaded_files/')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    content_type = models.CharField(max_length=100)
    size = models.IntegerField()
    processed = models.BooleanField(default=False)
    extracted_text = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    classification_result = models.ForeignKey(
        'classifier.ClassificationResult',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name

class TextInput(models.Model):
    """Model for storing manually input text"""
    content = models.TextField()
    title = models.CharField(max_length=255, blank=True)
    processed = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    classification_results = models.ManyToManyField('classifier.ClassificationResult', blank=True)
    llm_provider = models.CharField(max_length=50, default='unknown')
    llm_model = models.CharField(max_length=50, default='unknown')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
