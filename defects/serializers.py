from rest_framework import serializers
from .models import DefectReport, Comment, Product

class DefectReportSerializer(serializers.ModelSerializer):
    """Serializer for creating and viewing defect reports."""

    class Meta:
        model = DefectReport
        fields = [
            'id',
            'title',
            'description',
            'steps_to_reproduce',
            'product',
            'tester_id',
            'tester_email',
            'status',
            'severity',
            'priority',
            'assigned_developer',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'severity',
            'priority',
            'assigned_developer',
            'created_at',
            'updated_at',
        ]
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'
        # Ensure the user cannot manually override these via the API body
        read_only_fields = ['id', 'defect', 'author', 'created_at']
