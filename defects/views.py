from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json

from .models import DefectReport, Developer, Product
from .serializers import DefectReportSerializer, ResolveDefectSerializer


@api_view(['POST'])
def submit_defect(request):
    """
    Submit a new defect report.

    POST /api/defects/

    The defect is created with status='New'.
    If tester provided an email, we notify the Product Owner.
    """
    serializer = DefectReportSerializer(data=request.data)

    if serializer.is_valid():
        defect = serializer.save()

        # product_owner_email = defect.product.owner.email
        # if product_owner_email:
        #     send_mail(
        #         subject=f'[BetaTrax] New defect submitted: {defect.title}',
        #         message=f'A new defect has been submitted.\n\n'
        #                 f'Title: {defect.title}\n'
        #                 f'Tester ID: {defect.tester_id}\n'
        #                 f'Description: {defect.description}\n',
        #         from_email='betatrax@example.com',
        #         recipient_list=[product_owner_email],
        #     )

        return Response(
            DefectReportSerializer(defect).data,
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@login_required
@require_http_methods(["GET"])
def list_open_defects(request):
    """
    List all open defects (status='Open') available for the developer to take responsibility for.
    The developer must be associated with a product.
    """
    try:
        # Get the developer associated with the logged-in user
        developer = Developer.objects.get(user=request.user)
    except Developer.DoesNotExist:
        return JsonResponse(
            {'error': 'User is not a registered developer'},
            status=403
        )

    # Get all open defects for the developer's product
    open_defects = DefectReport.objects.filter(
        product=developer.product,
        status='Open'
    ).values('id', 'title', 'description', 'severity', 'priority', 'created_at')

    return JsonResponse({
        'product': developer.product.name,
        'open_defects': list(open_defects),
        'count': open_defects.count()
    })


@login_required
@require_http_methods(["POST"])
def take_responsibility(request, defect_id):
    """
    Developer takes responsibility for a defect.
    Changes status from 'Open' to 'Assigned' and links the defect to the developer.
    """
    try:
        developer = Developer.objects.get(user=request.user)
    except Developer.DoesNotExist:
        return JsonResponse(
            {'error': 'User is not a registered developer'},
            status=403
        )

    # Get the defect report
    defect = get_object_or_404(DefectReport, id=defect_id)

    # Verify the defect belongs to the developer's product
    if defect.product != developer.product:
        return JsonResponse(
            {'error': 'Defect does not belong to your product'},
            status=403
        )

    # Verify the defect status is 'Open'
    if defect.status != 'Open':
        return JsonResponse(
            {'error': f'Defect status must be Open, currently {defect.status}'},
            status=400
        )

    # Update the defect status and assign to developer
    defect.status = 'Assigned'
    defect.assigned_developer = developer
    defect.save()

    return JsonResponse({
        'success': True,
        'message': f'You have taken responsibility for defect {defect_id}',
        'defect': {
            'id': defect.id,
            'title': defect.title,
            'status': defect.status,
            'assigned_to': developer.user.username
        }
    })


@login_required
@require_http_methods(["GET"])
def view_defect_detail(request, defect_id):
    """
    View details of a specific defect report.
    Developer can view any defect in their product; other users can only view if assigned to them.
    """
    try:
        developer = Developer.objects.get(user=request.user)
    except Developer.DoesNotExist:
        return JsonResponse(
            {'error': 'You are not a registered developer'},
            status=403
        )

    defect = get_object_or_404(DefectReport, id=defect_id)

    # Verify access: developer can view defects from their product
    if defect.product != developer.product:
        return JsonResponse(
            {'error': 'You do not have access to this defect'},
            status=403
        )

    return JsonResponse({
        'id': defect.id,
        'title': defect.title,
        'description': defect.description,
        'steps_to_reproduce': defect.steps_to_reproduce,
        'product': defect.product.name,
        'tester_id': defect.tester_id,
        'tester_email': defect.tester_email,
        'status': defect.status,
        'severity': defect.severity,
        'priority': defect.priority,
        'assigned_developer': defect.assigned_developer.user.username if defect.assigned_developer else None,
        'created_at': defect.created_at.isoformat(),
        'updated_at': defect.updated_at.isoformat()
    })


@login_required
@require_http_methods(["POST"])
def mark_as_fixed(request, defect_id):
    """
    Developer marks a defect as Fixed.
    Can only be done if the defect is assigned to the developer.
    """
    try:
        developer = Developer.objects.get(user=request.user)
    except Developer.DoesNotExist:
        return JsonResponse(
            {'error': 'You are not a registered developer'},
            status=403
        )

    defect = get_object_or_404(DefectReport, id=defect_id)

    # Verify the defect is assigned to this developer
    if defect.assigned_developer != developer:
        return JsonResponse(
            {'error': 'Defect is not assigned to you'},
            status=403
        )

    # Verify the defect status is 'Assigned'
    if defect.status != 'Assigned':
        return JsonResponse(
            {'error': f'Defect status must be Assigned, currently {defect.status}'},
            status=400
        )

    # Update the defect status to 'Fixed'
    defect.status = 'Fixed'
    defect.save()

    return JsonResponse({
        'success': True,
        'message': f'Defect {defect_id} marked as Fixed',
        'defect': {
            'id': defect.id,
            'title': defect.title,
            'status': defect.status
        }
    })


@login_required
@require_http_methods(["POST"])
def mark_as_cannot_reproduce(request, defect_id):
    """
    Developer marks a defect as Cannot Reproduce.
    Can only be done if the defect is assigned to the developer.
    """
    try:
        developer = Developer.objects.get(user=request.user)
    except Developer.DoesNotExist:
        return JsonResponse(
            {'error': 'You are not a registered developer'},
            status=403
        )

    defect = get_object_or_404(DefectReport, id=defect_id)

    # Verify the defect is assigned to this developer
    if defect.assigned_developer != developer:
        return JsonResponse(
            {'error': 'Defect is not assigned to you'},
            status=403
        )

    # Verify the defect status is 'Assigned'
    if defect.status != 'Assigned':
        return JsonResponse(
            {'error': f'Defect status must be Assigned, currently {defect.status}'},
            status=400
        )

    # Update the defect status to 'Cannot Reproduce'
    defect.status = 'Cannot Reproduce'
    defect.save()

    return JsonResponse({
        'success': True,
        'message': f'Defect {defect_id} marked as Cannot Reproduce',
        'defect': {
            'id': defect.id,
            'title': defect.title,
            'status': defect.status
        }
    })


@api_view(['PATCH'])
def resolve_defect(request, pk):
    try:
        defect = DefectReport.objects.get(pk=pk)
    except DefectReport.DoesNotExist:
        return Response({"error": "Defect not found"}, status=status.HTTP_404_NOT_FOUND)

    # p0
    serializer = ResolveDefectSerializer(defect, data=request.data, partial=True)

    if serializer.is_valid():
        # target resolved only when fixed
        if defect.status != 'Fixed' and request.data.get('status') == 'Resolved':
             return Response({"error": "Only Fixed defects can be resolved."}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({"message": f"Defect {pk} marked as Resolved."})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
