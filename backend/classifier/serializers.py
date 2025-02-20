from rest_framework import serializers
from .models import ClassificationRule, ClassificationResult, ProcessingJob, CategoryGroup, Category

class ClassificationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassificationRule
        fields = ['id', 'name', 'description', 'rule_type', 'pattern', 
                 'priority', 'is_active', 'created_at', 'updated_at']

class ClassificationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassificationResult
        fields = ['id', 'content_type', 'content_hash', 'classification', 
                 'confidence', 'metadata', 'created_at', 'category_group_id',
                 'llm_provider', 'llm_model', 'user']
        read_only_fields = ['user']

class ProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingJob
        fields = ['id', 'status', 'job_type', 'input_data', 'output_data', 
                 'error_message', 'created_at', 'updated_at', 'user']
        read_only_fields = ['user']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at']

class CategoryGroupSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = CategoryGroup
        fields = ['id', 'name', 'description', 'is_active', 'categories', 
                 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        categories_data = self.context.get('categories', [])
        group = CategoryGroup.objects.create(**validated_data)
        
        for category_data in categories_data:
            Category.objects.create(group=group, **category_data)
        
        return group 