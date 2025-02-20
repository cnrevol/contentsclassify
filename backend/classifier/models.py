from django.db import models
from django.contrib.auth.models import User

class CategoryGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Category(models.Model):
    group = models.ForeignKey(CategoryGroup, related_name='categories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['group', 'name']

    def __str__(self):
        return f"{self.group.name} - {self.name}"

class ClassificationRule(models.Model):
    """Model for storing classification rules"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    rule_type = models.CharField(max_length=50)
    pattern = models.TextField()
    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ClassificationResult(models.Model):
    """Model for storing classification results"""
    content_type = models.CharField(max_length=50)
    content_hash = models.CharField(max_length=64)
    classification = models.CharField(max_length=100)
    confidence = models.FloatField()
    metadata = models.JSONField(default=dict)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category_group = models.ForeignKey(CategoryGroup, on_delete=models.SET_NULL, null=True)
    llm_provider = models.CharField(max_length=50, default='unknown')
    llm_model = models.CharField(max_length=50, default='unknown')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.classification} ({self.confidence})"

class ProcessingJob(models.Model):
    """Model for tracking processing jobs"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    job_type = models.CharField(max_length=50)
    input_data = models.JSONField()
    output_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.job_type} - {self.status}"
