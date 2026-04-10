from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import DefectReport, Developer, Product
from .serializers import DefectReportSerializer
from .services import ProductOwnerService


@api_view(['GET', 'POST'])
def defect_list(request):
    """
    POST /api/defects/   Submit a new defect report (no authentication required).
    GET  /api/defects/   List defects for the authenticated user's product.
                         Optional ?status= query param to filter by status.
    """
    if request.method == 'POST':
        serializer = DefectReportSerializer(data=request.data)
        if serializer.is_valid():
            defect = serializer.save()
            return Response(
                DefectReportSerializer(defect).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # GET — requires authentication
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    status_filter = request.query_params.get('status')

    # Try as developer
    try:
        developer = Developer.objects.get(user=request.user)
        defects = DefectReport.objects.filter(product=developer.product)
        if status_filter:
            defects = defects.filter(status=status_filter)
        defects = defects.values('id', 'title', 'description', 'severity', 'priority', 'created_at')
        return Response({
            'product': developer.product.name,
            'defects': list(defects),
            'count': defects.count()
        })
    except Developer.DoesNotExist:
        pass

    # Try as Product Owner
    po_service = ProductOwnerService(request.user)
    if not po_service.product:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    defects = po_service.get_defect_list()
    if status_filter:
        defects = defects.filter(status=status_filter)
    data = [{
        'report_id': d.id,
        'title': d.title,
        'tester_id': d.tester_id,
        'submitted_at': d.created_at,
        'status': d.status
    } for d in defects]
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def defect_detail(request, defect_id):
    """
    GET /api/defects/<defect_id>/   View full details of a defect report.
    Works for both developers and Product Owners; response shape differs by role.
    """
    # Try as developer
    try:
        developer = Developer.objects.get(user=request.user)
        defect = get_object_or_404(DefectReport, id=defect_id)
        if defect.product != developer.product:
            return Response(
                {'error': 'You do not have access to this defect'},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response({
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
    except Developer.DoesNotExist:
        pass

    # Try as Product Owner
    po_service = ProductOwnerService(request.user)
    if not po_service.product:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    defect = po_service.get_defect_detail(defect_id)
    if not defect:
        return Response({'error': 'Defect not found'}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        'report_id': defect.id,
        'product': defect.product.name,
        'title': defect.title,
        'description': defect.description,
        'reproduction_steps': defect.steps_to_reproduce,
        'tester_id': defect.tester_id,
        'tester_email': defect.tester_email,
        'status': defect.status,
        'submitted_at': defect.created_at
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def take_responsibility(request, defect_id):
    """
    Developer takes responsibility for a defect.
    Changes status from 'Open' to 'Assigned' and links the defect to the developer.
    """
    try:
        developer = Developer.objects.get(user=request.user)
    except Developer.DoesNotExist:
        return Response(
            {'error': 'User is not a registered developer'},
            status=status.HTTP_403_FORBIDDEN
        )

    defect = get_object_or_404(DefectReport, id=defect_id)

    if defect.product != developer.product:
        return Response(
            {'error': 'Defect does not belong to your product'},
            status=status.HTTP_403_FORBIDDEN
        )

    if defect.status != 'Open':
        return Response(
            {'error': f'Defect status must be Open, currently {defect.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    defect.status = 'Assigned'
    defect.assigned_developer = developer
    defect.save()

    return Response({
        'success': True,
        'message': f'You have taken responsibility for defect {defect_id}',
        'defect': {
            'id': defect.id,
            'title': defect.title,
            'status': defect.status,
            'assigned_to': developer.user.username
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_fixed(request, defect_id):
    """
    Developer marks a defect as Fixed.
    Can only be done if the defect is assigned to the developer.
    """
    try:
        developer = Developer.objects.get(user=request.user)
    except Developer.DoesNotExist:
        return Response(
            {'error': 'You are not a registered developer'},
            status=status.HTTP_403_FORBIDDEN
        )

    defect = get_object_or_404(DefectReport, id=defect_id)

    if defect.assigned_developer != developer:
        return Response(
            {'error': 'Defect is not assigned to you'},
            status=status.HTTP_403_FORBIDDEN
        )

    if defect.status != 'Assigned':
        return Response(
            {'error': f'Defect status must be Assigned, currently {defect.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    defect.status = 'Fixed'
    defect.save()

    return Response({
        'success': True,
        'message': f'Defect {defect_id} marked as Fixed',
        'defect': {
            'id': defect.id,
            'title': defect.title,
            'status': defect.status
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_cannot_reproduce(request, defect_id):
    """
    Developer marks a defect as Cannot Reproduce.
    Can only be done if the defect is assigned to the developer.
    """
    try:
        developer = Developer.objects.get(user=request.user)
    except Developer.DoesNotExist:
        return Response(
            {'error': 'You are not a registered developer'},
            status=status.HTTP_403_FORBIDDEN
        )

    defect = get_object_or_404(DefectReport, id=defect_id)

    if defect.assigned_developer != developer:
        return Response(
            {'error': 'Defect is not assigned to you'},
            status=status.HTTP_403_FORBIDDEN
        )

    if defect.status != 'Assigned':
        return Response(
            {'error': f'Defect status must be Assigned, currently {defect.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    defect.status = 'Cannot Reproduce'
    defect.save()

    return Response({
        'success': True,
        'message': f'Defect {defect_id} marked as Cannot Reproduce',
        'defect': {
            'id': defect.id,
            'title': defect.title,
            'status': defect.status
        }
    })
