from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.utils import timezone

from .models import DefectReport, Employee
from .serializers import DefectReportSerializer


def _send_notification(defect, old_status, new_status):
    if not defect.tester_email:
        return
    subject = f"BetaTrax: Defect Report {defect.id} Status Updated"
    message = f"""
    Defect Report ID: {defect.id}
    Title: {defect.title}
    Old Status: {old_status}
    New Status: {new_status}
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email='noreply@betatrax.com',
            recipient_list=[defect.tester_email],
            fail_silently=False,
        )
    except Exception:
        pass


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

    # GET — listing requires a logged in user
    if not request.user.is_authenticated:
        return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    status_filter = request.query_params.get('status')
    defects = DefectReport.objects.filter(product=employee.product)
    if status_filter:
        defects = defects.filter(status=status_filter)

    if employee.role == 'Developer':
        defects = defects.values('id', 'title', 'description', 'severity', 'priority', 'created_at')
        return Response({
            'product': employee.product.name,
            'defects': list(defects),
            'count': defects.count()
        })

    # Product Owner
    defects = defects.order_by('-created_at')
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
    Response shape differs by role.
    """
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    defect = get_object_or_404(DefectReport, id=defect_id, product=employee.product)

    if employee.role == 'Developer':
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

    # Product Owner
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
        employee = Employee.objects.get(user=request.user, role='Developer')
    except Employee.DoesNotExist:
        return Response(
            {'error': 'User is not a registered developer'},
            status=status.HTTP_403_FORBIDDEN
        )

    defect = get_object_or_404(DefectReport, id=defect_id)

    if defect.product != employee.product:
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
    defect.assigned_developer = employee
    defect.save()

    return Response({
        'success': True,
        'message': f'You have taken responsibility for defect {defect_id}',
        'defect': {
            'id': defect.id,
            'title': defect.title,
            'status': defect.status,
            'assigned_to': employee.user.username
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_fixed(request, defect_id):
    """
    Developer marks a defect as Fixed.
    Can only be done if the defect is assigned to this developer.
    """
    try:
        employee = Employee.objects.get(user=request.user, role='Developer')
    except Employee.DoesNotExist:
        return Response(
            {'error': 'You are not a registered developer'},
            status=status.HTTP_403_FORBIDDEN
        )

    defect = get_object_or_404(DefectReport, id=defect_id)

    if defect.assigned_developer != employee:
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
    Can only be done if the defect is assigned to this developer.
    """
    try:
        employee = Employee.objects.get(user=request.user, role='Developer')
    except Employee.DoesNotExist:
        return Response(
            {'error': 'You are not a registered developer'},
            status=status.HTTP_403_FORBIDDEN
        )

    defect = get_object_or_404(DefectReport, id=defect_id)

    if defect.assigned_developer != employee:
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_defect(request, defect_id):
    """
    PO approves a New defect report — sets severity/priority, creates backlog link, moves to Open.
    """
    try:
        po = Employee.objects.get(user=request.user, role='ProductOwner')
    except Employee.DoesNotExist:
        return Response({'error': 'User is not a Product Owner'}, status=status.HTTP_403_FORBIDDEN)

    try:
        defect = DefectReport.objects.get(id=defect_id, product=po.product, status='New')
    except DefectReport.DoesNotExist:
        return Response({'error': 'Defect not found or not New status'}, status=status.HTTP_400_BAD_REQUEST)

    severity = request.data.get('severity')
    priority = request.data.get('priority')
    backlog_item_id = request.data.get('backlog_item_id')

    if not all([severity, priority, backlog_item_id]):
        return Response(
            {'error': 'Severity, Priority and Backlog Item are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    defect.severity = severity
    defect.priority = priority
    defect.status = 'Open'
    defect.approved_by = request.user
    defect.approved_at = timezone.now()
    defect.backlog_item_link = backlog_item_id
    defect.save()

    _send_notification(defect, old_status='New', new_status='Open')

    return Response({
        'success': True,
        'message': 'Report Approved and Marked as Open',
        'report_id': defect.id,
        'new_status': 'Open'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_defect(request, defect_id):
    """
    PO confirms a fix passes retesting — moves status from Fixed to Resolved.
    """
    try:
        po = Employee.objects.get(user=request.user, role='ProductOwner')
    except Employee.DoesNotExist:
        return Response({'error': 'User is not a Product Owner'}, status=status.HTTP_403_FORBIDDEN)

    # must be Fixed before we can resolve
    try:
        defect = DefectReport.objects.get(id=defect_id, product=po.product, status='Fixed')
    except DefectReport.DoesNotExist:
        return Response({'error': 'Defect not found or not Fixed status'}, status=status.HTTP_400_BAD_REQUEST)

    defect.status = 'Resolved'
    defect.save()
    _send_notification(defect, old_status='Fixed', new_status='Resolved')

    return Response({
        'success': True,
        'message': f'Defect {defect_id} marked as Resolved.',
        'report_id': defect.id,
        'new_status': 'Resolved'
    })
