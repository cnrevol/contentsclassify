from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import ProcessedFile, TextInput
from .serializers import ProcessedFileSerializer, TextInputSerializer
from .services import FileProcessingService
import logging
from rest_framework.exceptions import APIException
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger('fileapp')

class FileUploadView(generics.CreateAPIView):
    """View for uploading files"""
    parser_classes = (MultiPartParser, FormParser)
    serializer_class = ProcessedFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        file_obj = self.request.FILES.get('file')
        if not file_obj:
            raise ValueError("No file was submitted")

        # Create ProcessedFile instance
        instance = serializer.save(
            user=self.request.user,
            file=file_obj,
            file_name=file_obj.name,
            size=file_obj.size,
            content_type=file_obj.content_type
        )

        # Process the file
        processing_service = FileProcessingService()
        processing_service.process_file(instance)

class ProcessedFileListView(generics.ListAPIView):
    """View for listing processed files"""
    serializer_class = ProcessedFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProcessedFile.objects.filter(user=self.request.user)

class ProcessedFileDetailView(generics.RetrieveDestroyAPIView):
    """View for retrieving and deleting processed files"""
    serializer_class = ProcessedFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProcessedFile.objects.filter(user=self.request.user)

class TextInputPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class TextInputListCreateView(generics.ListCreateAPIView):
    """View for listing and creating text inputs"""
    serializer_class = TextInputSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TextInputPagination

    def get_queryset(self):
        """Return queryset ordered by created_at in descending order"""
        logger.info(f"Getting text inputs for user: {self.request.user.id}")
        queryset = TextInput.objects.filter(
            user=self.request.user
        ).order_by('-created_at')
        logger.info(f"Found {queryset.count()} text inputs")
        return queryset

    def perform_create(self, serializer):
        """Process the text input and create classification results"""
        text_input = serializer.save(user=self.request.user)
        
        try:
            # Get LLM provider from request data
            llm_provider = self.request.data.get('llm_provider', settings.DEFAULT_LLM_PROVIDER)
            
            # Initialize processing service
            processing_service = FileProcessingService()
            
            # Process the content with specified LLM provider
            results = processing_service.process_content(
                content=text_input.content,
                content_type='text',
                user=self.request.user if self.request.user.is_authenticated else None,
                llm_provider=llm_provider
            )
            
            # Update text input with classification results
            text_input.processed = True
            text_input.save()
            
            # Associate classification results with text input
            if isinstance(results, list):
                text_input.classification_results.set(results)
            elif results:
                text_input.classification_results.set([results])
            
            # Return updated serializer data
            return Response(self.get_serializer(text_input).data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error processing text input: {str(e)}", exc_info=True)
            text_input.delete()
            raise APIException(f"Failed to process text input: {str(e)}")

    def create(self, request, *args, **kwargs):
        """Override create to handle the response from perform_create"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = self.perform_create(serializer)
        if isinstance(response, Response):
            return response
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class TextInputDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating and deleting text inputs"""
    serializer_class = TextInputSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return TextInput.objects.filter(user=self.request.user)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_llm_providers(request):
    """Get available LLM providers from settings"""
    providers = list(settings.LLM_PROVIDERS.keys())
    return Response({'providers': providers})
