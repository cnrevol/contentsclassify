from rest_framework import serializers
from .models import EmailAccount, EmailMessage, EmailAttachment, EmailFile, EmailClassificationRule

class EmailAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAccount
        fields = ['id', 'email', 'server_type', 'server_host', 'server_port',
                 'username', 'password', 'is_active', 'last_checked',
                 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True}
        }

class EmailAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailAttachment
        fields = ['id', 'email', 'file_name', 'content_type', 'size',
                 'file', 'processed', 'classification_result', 'created_at']

class EmailMessageSerializer(serializers.ModelSerializer):
    attachments = EmailAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = EmailMessage
        fields = ['id', 'account', 'message_id', 'subject', 'sender',
                 'recipients', 'content', 'attachments', 'received_date',
                 'processed', 'classification_result', 'created_at']

class EmailFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailFile
        fields = [
            'id', 
            'file', 
            'file_name', 
            'file_type',
            'size',
            'processed',
            'email_content',
            'classification_result',
            'classification_level',
            'confidence_score',
            'processing_time',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'file_name',
            'file_type',
            'size',
            'processed',
            'email_content',
            'classification_result',
            'classification_level',
            'confidence_score',
            'processing_time',
            'created_at'
        ]

class EmailClassificationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailClassificationRule
        fields = '__all__' 