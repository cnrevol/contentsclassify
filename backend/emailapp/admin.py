from django.contrib import admin
from .models import EmailClassificationRule

@admin.register(EmailClassificationRule)
class EmailClassificationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'classification', 'priority', 'is_active')
    list_filter = ('is_active', 'classification')
    search_fields = ('name', 'description', 'classification')
    ordering = ('-priority',)
