from rest_framework import serializers
from .models import DefectReport


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
