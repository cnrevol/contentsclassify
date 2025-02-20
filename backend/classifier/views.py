from django.shortcuts import render
from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework import status
from .models import ClassificationRule, ClassificationResult, ProcessingJob, CategoryGroup, Category
from .serializers import (
    ClassificationRuleSerializer,
    ClassificationResultSerializer,
    ProcessingJobSerializer,
    CategoryGroupSerializer,
    CategorySerializer
)
import logging
from rest_framework.decorators import action

logger = logging.getLogger('classifier')

class ClassificationRuleListCreateView(generics.ListCreateAPIView):
    """View for listing and creating classification rules"""
    queryset = ClassificationRule.objects.all()
    serializer_class = ClassificationRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

class ClassificationRuleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating and deleting classification rules"""
    queryset = ClassificationRule.objects.all()
    serializer_class = ClassificationRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

class ClassificationResultListView(generics.ListAPIView):
    """View for listing classification results"""
    serializer_class = ClassificationResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ClassificationResult.objects.filter(user=self.request.user)

class ClassificationResultDetailView(generics.RetrieveAPIView):
    """View for retrieving classification results"""
    serializer_class = ClassificationResultSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ClassificationResult.objects.filter(user=self.request.user)

class ProcessingJobListCreateView(generics.ListCreateAPIView):
    """View for listing and creating processing jobs"""
    serializer_class = ProcessingJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProcessingJob.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProcessingJobDetailView(generics.RetrieveAPIView):
    """View for retrieving processing job details"""
    serializer_class = ProcessingJobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ProcessingJob.objects.filter(user=self.request.user)

class CategoryGroupListCreateView(generics.ListCreateAPIView):
    queryset = CategoryGroup.objects.all()
    serializer_class = CategoryGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating new category group with data: {request.data}")
        try:
            categories_data = request.data.pop('categories', [])
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            category_group = serializer.save(created_by=request.user)
            
            # Create categories
            for category_data in categories_data:
                logger.debug(f"Creating category in group {category_group.id}: {category_data}")
                Category.objects.create(group=category_group, **category_data)
            
            logger.info(f"Successfully created category group {category_group.id} with {len(categories_data)} categories")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating category group: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CategoryGroupDetailView(viewsets.ModelViewSet):
    """ViewSet for managing category groups"""
    queryset = CategoryGroup.objects.all()
    serializer_class = CategoryGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """Create a new category group"""
        logger.info(f"Creating new category group with data: {request.data}")
        try:
            categories_data = request.data.pop('categories', [])
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            category_group = serializer.save(created_by=request.user)
            
            # Create categories
            for category_data in categories_data:
                logger.debug(f"Creating category in group {category_group.id}: {category_data}")
                Category.objects.create(group=category_group, **category_data)
            
            logger.info(f"Successfully created category group {category_group.id} with {len(categories_data)} categories")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating category group: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle the active status of a category group"""
        logger.info(f"Toggling active status for category group {pk}")
        try:
            group = self.get_object()
            group.is_active = not group.is_active
            group.save()
            
            logger.info(f"Successfully {'activated' if group.is_active else 'deactivated'} category group {pk}")
            return Response({
                'id': group.id,
                'is_active': group.is_active,
                'message': f"Category group {group.name} has been {'activated' if group.is_active else 'deactivated'}"
            })
        except Exception as e:
            logger.error(f"Error toggling active status: {str(e)}")
            return Response(
                {"error": f"Failed to toggle active status: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        logger.info(f"Updating category group {kwargs.get('pk')} with data: {request.data}")
        try:
            instance = self.get_object()
            categories_data = request.data.pop('categories', [])
            
            # Update category group
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            category_group = serializer.save()
            
            # Update categories
            logger.debug(f"Deleting existing categories for group {category_group.id}")
            instance.categories.all().delete()
            
            for category_data in categories_data:
                logger.debug(f"Creating updated category in group {category_group.id}: {category_data}")
                Category.objects.create(group=category_group, **category_data)
            
            logger.info(f"Successfully updated category group {category_group.id} with {len(categories_data)} categories")
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error updating category group: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        logger.info(f"Deleting category group {kwargs.get('pk')}")
        try:
            instance = self.get_object()
            instance.delete()
            logger.info(f"Successfully deleted category group {kwargs.get('pk')}")
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error deleting category group: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        group_id = self.kwargs.get('group_id')
        return Category.objects.filter(group_id=group_id)

    def perform_create(self, serializer):
        group_id = self.kwargs.get('group_id')
        group = CategoryGroup.objects.get(id=group_id)
        serializer.save(group=group)
