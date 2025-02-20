from rest_framework import serializers
from .models import ProcessedFile, TextInput
from classifier.serializers import ClassificationResultSerializer

class ProcessedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessedFile
        fields = ['id', 'user', 'file', 'file_name', 'file_type',
                 'content_type', 'size', 'processed', 'extracted_text',
                 'metadata', 'classification_result', 'created_at',
                 'updated_at']
        read_only_fields = ['user', 'file_name', 'file_type', 'content_type',
                           'size', 'processed', 'extracted_text', 'metadata',
                           'classification_result']

class TextInputSerializer(serializers.ModelSerializer):
    classification_results = ClassificationResultSerializer(many=True, read_only=True)
    
    class Meta:
        model = TextInput
        fields = ['id', 'user', 'content', 'title', 'processed', 'metadata', 'classification_results', 'created_at', 'updated_at']
        read_only_fields = ['user', 'processed', 'classification_results'] 