from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .metrics import classify_effectiveness
from .models import DefectReport, Employee, Comment, Product
from .serializers import DefectReportSerializer, CommentSerializer, ProductSerializer


def _get_employee(request, role=None):
    if not request.user.is_authenticated:
        return None, Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        employee = Employee.objects.select_related('user', 'product').get(user=request.user)
    except Employee.DoesNotExist:
        return None, Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

    if role and employee.role != role:
        return None, Response({'error': f'User is not a registered {role.lower()}'}, status=status.HTTP_403_FORBIDDEN)

    return employee, None


def _product_owner_email(product):
    owner = product.employees.select_related('user').filter(role='ProductOwner').first()
    return owner.user.email if owner and owner.user.email else None


def _collect_duplicate_dependents(defect, visited=None):
    if visited is None:
        visited = set()

    dependents = []
    for child in defect.duplicates.all():
        if child.id in visited:
            continue
        visited.add(child.id)
        dependents.append(child)
        dependents.extend(_collect_duplicate_dependents(child, visited))
    return dependents


def send_status_change_notifications(defect, old_status, new_status):
    if defect.tester_email:
        try:
            send_mail(
                subject=f'BetaTrax: Defect Report {defect.id} Status Updated',
                message=(
                    f'Defect Report ID: {defect.id}\n'
                    f'Title: {defect.title}\n'
                    f'Old Status: {old_status}\n'
                    f'New Status: {new_status}\n'
                ),
                from_email='system@betatrax.com',
                recipient_list=[defect.tester_email],
                fail_silently=False,
            )
        except Exception:
            pass

    for dependent in _collect_duplicate_dependents(defect):
        if not dependent.tester_email:
            continue
        try:
            send_mail(
                subject=f'BetaTrax: Parent Defect {defect.id} Status Updated',
                message=(
                    f'Defect Report ID: {dependent.id}\n'
                    f'Title: {dependent.title}\n'
                    f'Parent Defect ID: {defect.id}\n'
                    f'Parent Title: {defect.title}\n'
                    f'Parent Old Status: {old_status}\n'
                    f'Parent New Status: {new_status}\n'
                ),
                from_email='system@betatrax.com',
                recipient_list=[dependent.tester_email],
                fail_silently=False,
            )
        except Exception:
            pass


@extend_schema(methods=['GET'], operation_id='defects_list_get', responses=None)
@extend_schema(methods=['POST'], operation_id='defects_list_post', request=DefectReportSerializer, responses=DefectReportSerializer)
@api_view(['GET', 'POST'])
def defect_list(request):
    if request.method == 'POST':
        serializer = DefectReportSerializer(data=request.data)
        if serializer.is_valid():
            defect = serializer.save()
            return Response(DefectReportSerializer(defect).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    employee, error_response = _get_employee(request)
    if error_response:
        return error_response

    defects = DefectReport.objects.filter(product=employee.product)

    status_filter = request.query_params.get('status')
    severity_filter = request.query_params.get('severity')
    priority_filter = request.query_params.get('priority')
    assigned_to_filter = request.query_params.get('assigned_to')
    tester_id_filter = request.query_params.get('tester_id')

    if status_filter:
        defects = defects.filter(status=status_filter)
    if severity_filter:
        defects = defects.filter(severity=severity_filter)
    if priority_filter:
        defects = defects.filter(priority=priority_filter)
    if assigned_to_filter:
        defects = defects.filter(assigned_developer_id=assigned_to_filter)
    if tester_id_filter:
        defects = defects.filter(tester_id=tester_id_filter)

    if employee.role == 'Developer':
        defects = defects.values('id', 'title', 'description', 'severity', 'priority', 'created_at')
        return Response({
            'product': employee.product.name,
            'defects': list(defects),
            'count': defects.count()
        })

    defects = defects.order_by('-created_at')
    return Response([
        {
            'report_id': defect.id,
            'title': defect.title,
            'tester_id': defect.tester_id,
            'submitted_at': defect.created_at,
            'status': defect.status
        }
        for defect in defects
    ])


@extend_schema(operation_id='defects_detail', responses=None)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def defect_detail(request, defect_id):
    return _defect_detail_response(request, defect_id)


def _defect_detail_response(request, defect_id):
    employee, error_response = _get_employee(request)
    if error_response:
        return error_response

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

    return Response({
        'report_id': defect.id,
        'product': defect.product.name,
        'title': defect.title,
        'description': defect.description,
        'reproduction_steps': defect.steps_to_reproduce,
        'tester_id': defect.tester_id,
        'tester_email': defect.tester_email,
        'status': defect.status,
        'duplicate_of_report_id': defect.duplicate_of.id if defect.duplicate_of else None,
        'rejection_reason': defect.rejection_reason,
        'rejected_at': defect.rejected_at,
        'reopen_reason': defect.reopen_reason,
        'reopened_at': defect.reopened_at,
        'reopened_by': defect.reopened_by.username if defect.reopened_by else None,
        'cannot_reproduce_reason': defect.cannot_reproduce_reason,
        'submitted_at': defect.created_at
    })


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def take_responsibility(request, defect_id):
    employee, error_response = _get_employee(request, role='Developer')
    if error_response:
        return error_response

    defect = get_object_or_404(DefectReport, id=defect_id)

    if defect.product != employee.product:
        return Response({'error': 'Defect does not belong to your product'}, status=status.HTTP_403_FORBIDDEN)

    if defect.status not in ['Open', 'Reopened']:
        return Response({'error': f'Defect status must be Open or Reopened, currently {defect.status}'}, status=status.HTTP_400_BAD_REQUEST)

    defect.status = 'Assigned'
    defect.assigned_developer = employee
    defect.save()
    send_status_change_notifications(defect, 'Open', 'Assigned')

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


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_fixed(request, defect_id):
    employee, error_response = _get_employee(request, role='Developer')
    if error_response:
        return error_response

    defect = get_object_or_404(DefectReport, id=defect_id)

    if defect.product != employee.product:
        return Response({'error': 'Defect does not belong to your product'}, status=status.HTTP_403_FORBIDDEN)

    if defect.assigned_developer != employee:
        return Response({'error': 'Defect is not assigned to you'}, status=status.HTTP_403_FORBIDDEN)

    if defect.status != 'Assigned':
        return Response({'error': f'Defect status must be Assigned, currently {defect.status}'}, status=status.HTTP_400_BAD_REQUEST)

    defect.status = 'Fixed'
    defect.save()

    employee.defects_fixed_count += 1
    employee.save()

    send_status_change_notifications(defect, 'Assigned', 'Fixed')

    return Response({
        'success': True,
        'message': f'Defect {defect_id} marked as Fixed',
        'defect': {
            'id': defect.id,
            'title': defect.title,
            'status': defect.status
        }
    })


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_cannot_reproduce(request, defect_id):
    employee, error_response = _get_employee(request, role='Developer')
    if error_response:
        return error_response

    defect = get_object_or_404(DefectReport, id=defect_id)

    if defect.product != employee.product:
        return Response({'error': 'Defect does not belong to your product'}, status=status.HTTP_403_FORBIDDEN)

    if defect.assigned_developer != employee:
        return Response({'error': 'Defect is not assigned to you'}, status=status.HTTP_403_FORBIDDEN)

    reason = request.data.get('cannot_reproduce_reason')
    if not reason or not str(reason).strip():
        return Response({'error': 'cannot_reproduce_reason is required'}, status=status.HTTP_400_BAD_REQUEST)

    if defect.status != 'Assigned':
        return Response({'error': f'Defect status must be Assigned, currently {defect.status}'}, status=status.HTTP_400_BAD_REQUEST)

    defect.status = 'Cannot Reproduce'
    defect.cannot_reproduce_reason = str(reason).strip()
    defect.cannot_reproduced_by = employee
    defect.cannot_reproduced_at = timezone.now()
    defect.save()

    send_status_change_notifications(defect, 'Assigned', 'Cannot Reproduce')

    po_email = _product_owner_email(defect.product)
    if po_email:
        try:
            send_mail(
                subject=f'BetaTrax: Defect {defect.id} Marked Cannot Reproduce',
                message=(
                    f'Defect Report ID: {defect.id}\n'
                    f'Title: {defect.title}\n'
                    f'New Status: Cannot Reproduce\n'
                    f'Developer ID: {employee.id}\n'
                    f'Reason: {defect.cannot_reproduce_reason}\n'
                ),
                from_email='system@betatrax.com',
                recipient_list=[po_email],
                fail_silently=False,
            )
        except Exception:
            pass

    return Response({
        'success': True,
        'message': f'Defect {defect_id} marked as Cannot Reproduce',
        'defect': {
            'id': defect.id,
            'title': defect.title,
            'status': defect.status,
            'cannot_reproduce_reason': defect.cannot_reproduce_reason,
            'cannot_reproduced_by': employee.id,
            'cannot_reproduced_at': defect.cannot_reproduced_at,
        }
    })


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_defect(request, defect_id):
    po, error_response = _get_employee(request, role='ProductOwner')
    if error_response:
        return error_response

    try:
        defect = DefectReport.objects.get(id=defect_id, product=po.product, status='New')
    except DefectReport.DoesNotExist:
        return Response({'error': 'Defect not found or not New status'}, status=status.HTTP_400_BAD_REQUEST)

    severity = request.data.get('severity')
    priority = request.data.get('priority')
    backlog_item_id = request.data.get('backlog_item_id')

    if not all([severity, priority, backlog_item_id]):
        return Response({'error': 'Severity, Priority and Backlog Item are required'}, status=status.HTTP_400_BAD_REQUEST)

    defect.severity = severity
    defect.priority = priority
    defect.status = 'Open'
    defect.approved_by = request.user
    defect.approved_at = timezone.now()
    defect.backlog_item_link = backlog_item_id
    defect.save()

    send_status_change_notifications(defect, 'New', 'Open')

    return Response({
        'success': True,
        'message': 'Report Approved and Marked as Open',
        'report_id': defect.id,
        'new_status': 'Open'
    })


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_defect(request, defect_id):
    po, error_response = _get_employee(request, role='ProductOwner')
    if error_response:
        return error_response

    try:
        defect = DefectReport.objects.get(id=defect_id, product=po.product, status='New')
    except DefectReport.DoesNotExist:
        return Response({'error': 'Defect not found or not New status'}, status=status.HTTP_400_BAD_REQUEST)

    rejection_reason = request.data.get('rejection_reason')
    if not rejection_reason or not str(rejection_reason).strip():
        return Response({'error': 'Rejection reason is required'}, status=status.HTTP_400_BAD_REQUEST)

    defect.status = 'Rejected'
    defect.rejection_reason = str(rejection_reason).strip()
    defect.rejected_by = request.user
    defect.rejected_at = timezone.now()
    defect.save()

    send_status_change_notifications(defect, 'New', 'Rejected')

    return Response({
        'success': True,
        'message': 'Report Rejected as Invalid',
        'report_id': defect.id,
        'new_status': 'Rejected',
        'rejection_reason': defect.rejection_reason,
    })


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_duplicate(request, defect_id):
    po, error_response = _get_employee(request, role='ProductOwner')
    if error_response:
        return error_response

    try:
        defect = DefectReport.objects.get(id=defect_id, product=po.product, status='New')
    except DefectReport.DoesNotExist:
        return Response({'error': 'Defect not found or not New status'}, status=status.HTTP_400_BAD_REQUEST)

    duplicate_of_report_id = request.data.get('duplicate_of_report_id')
    if not duplicate_of_report_id:
        return Response({'error': 'duplicate_of_report_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        duplicate_of_report_id = int(duplicate_of_report_id)
    except (TypeError, ValueError):
        return Response({'error': 'duplicate_of_report_id must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)

    if int(defect_id) == duplicate_of_report_id:
        return Response({'error': 'A defect cannot be marked duplicate of itself'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        original_defect = DefectReport.objects.get(id=duplicate_of_report_id, product=po.product)
    except DefectReport.DoesNotExist:
        return Response({'error': 'Original defect for duplication not found'}, status=status.HTTP_400_BAD_REQUEST)

    if original_defect.status == 'New':
        return Response({'error': 'Duplicate target must already be opened'}, status=status.HTTP_400_BAD_REQUEST)

    defect.duplicate_of = original_defect
    defect.status = 'Duplicate'
    defect.save()

    send_status_change_notifications(defect, 'New', 'Duplicate')

    return Response({
        'success': True,
        'message': 'Report Marked as Duplicate',
        'report_id': defect.id,
        'new_status': 'Duplicate',
        'duplicate_of_report_id': original_defect.id,
    })


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reopen_defect(request, defect_id):
    po, error_response = _get_employee(request, role='ProductOwner')
    if error_response:
        return error_response

    try:
        defect = DefectReport.objects.get(id=defect_id, product=po.product, status='Fixed')
    except DefectReport.DoesNotExist:
        return Response({'error': 'Defect not found or not Fixed status'}, status=status.HTTP_400_BAD_REQUEST)

    reopen_reason = request.data.get('reopen_reason')
    if not reopen_reason or not str(reopen_reason).strip():
        return Response({'error': 'Reopen reason is required'}, status=status.HTTP_400_BAD_REQUEST)

    # increment before clearing — once assigned_developer is None we lose the reference
    if defect.assigned_developer:
        defect.assigned_developer.defects_reopened_count += 1
        defect.assigned_developer.save()

    defect.status = 'Reopened'
    defect.reopen_reason = str(reopen_reason).strip()
    defect.reopened_by = request.user
    defect.reopened_at = timezone.now()
    defect.assigned_developer = None
    defect.save()

    send_status_change_notifications(defect, 'Fixed', 'Reopened')

    return Response({
        'success': True,
        'message': 'Report Marked as Reopened',
        'report_id': defect.id,
        'new_status': 'Reopened',
        'reopen_reason': defect.reopen_reason,
        'reopened_at': defect.reopened_at,
        'reopened_by': request.user.username,
    })


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_defect(request, defect_id):
    po, error_response = _get_employee(request, role='ProductOwner')
    if error_response:
        return error_response

    try:
        defect = DefectReport.objects.get(id=defect_id, product=po.product, status='Fixed')
    except DefectReport.DoesNotExist:
        return Response({'error': 'Defect not found or not Fixed status'}, status=status.HTTP_400_BAD_REQUEST)

    defect.status = 'Resolved'
    defect.save()

    send_status_change_notifications(defect, 'Fixed', 'Resolved')

    return Response({
        'success': True,
        'message': f'Defect {defect_id} marked as Resolved.',
        'report_id': defect.id,
        'new_status': 'Resolved'
    })


@extend_schema(methods=['GET'], responses=CommentSerializer(many=True))
@extend_schema(methods=['POST'], request=CommentSerializer, responses=CommentSerializer)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def defect_comments(request, defect_id):
    employee, error_response = _get_employee(request)
    if error_response:
        return error_response

    defect = get_object_or_404(DefectReport, id=defect_id, product=employee.product)

    if request.method == 'GET':
        comments = Comment.objects.filter(defect_report=defect).order_by('date')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    serializer = CommentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(defect_report=defect, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=ProductSerializer, responses=ProductSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_product(request):
    po, error_response = _get_employee(request, role='ProductOwner')
    if error_response:
        return error_response
    serializer = ProductSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=None, responses=None)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    if hasattr(request.user, 'auth_token'):
        request.user.auth_token.delete()
    return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)


@extend_schema(responses=None)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def developer_effectiveness(request, employee_id):
    requester, error_response = _get_employee(request)
    if error_response:
        return error_response

    developer = get_object_or_404(Employee, id=employee_id, product=requester.product, role='Developer')

    classification = classify_effectiveness(developer.defects_fixed_count, developer.defects_reopened_count)
    return Response({
        'employee_id': developer.id,
        'username': developer.user.username,
        'defects_fixed': developer.defects_fixed_count,
        'defects_reopened': developer.defects_reopened_count,
        'classification': classification,
    })
