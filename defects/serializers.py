from rest_framework import serializers
from .models import DefectReport
from django.core.mail import send_mail


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


class ResolveDefectSerializer(serializers.ModelSerializer):
    class Meta:
        model = DefectReport
        fields = ['status']

    def update(self, instance, validated_data):
        new_status = validated_data.get('status')

        # fixed -> resolved
        if instance.status == 'Fixed' and new_status == 'Resolved':
            instance.status = new_status
            instance.save()

            # Send email notification to tester
            if instance.tester_email:
                send_mail(
                    subject=f'Defect Resolved: {instance.title}',
                    message=f'Hello, the defect "{instance.title}" you reported has been resolved.',
                    from_email='noreply@betatrax.com',
                    recipient_list=[instance.tester_email],
                )
        return instance
