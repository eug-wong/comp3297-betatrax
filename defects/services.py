# services.py
from django.utils import timezone
from django.core.mail import send_mail
from .models import DefectReport, Product


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
                from_email='system@betatrax.com',
                recipient_list=[defect.tester_email],
                fail_silently=False,
            )
        except Exception:
            pass

    for dependent in _collect_duplicate_dependents(defect):
        if not dependent.tester_email:
            continue

        subject = f"BetaTrax: Parent Defect {defect.id} Status Updated"
        message = f"""
        Defect Report ID: {dependent.id}
        Title: {dependent.title}
        Parent Defect ID: {defect.id}
        Parent Title: {defect.title}
        Parent Old Status: {old_status}
        Parent New Status: {new_status}
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email='system@betatrax.com',
                recipient_list=[dependent.tester_email],
                fail_silently=False,
            )
        except Exception:
            pass

class ProductOwnerService:
    def __init__(self, po_user):
        self.po_user = po_user
        try:
            self.product = Product.objects.get(owner=po_user)
        except Product.DoesNotExist:
            self.product = None

    # 1. Get the New defect list of products responsible for PO
    def get_new_defect_list(self):
        if not self.product:
            return []
        return DefectReport.objects.filter(
            product=self.product,
            status='New'
        ).order_by('-created_at')

    def get_defect_list(self):
        if not self.product:
            return []
        return DefectReport.objects.filter(
            product=self.product,
        ).order_by('-created_at')

    # 2. Obtain detailed information of a single defect
    def get_defect_detail(self, report_id):
        if not self.product:
            return None
        try:
            return DefectReport.objects.get(id=report_id, product=self.product)
        except DefectReport.DoesNotExist:
            return None

    # 3. Verify that the field is required and then approve the defect, and update the status to Open
    def accept_and_approve_defect(
        self,
        report_id,
        severity,
        priority,
        backlog_item_id
    ):
        if not self.product:
            return {"success": False, "message": "User is not a Product Owner"}

        # Verify products and permissions
        try:
            defect = DefectReport.objects.get(
                id=report_id,
                product=self.product,
                status='New'
            )
        except DefectReport.DoesNotExist:
            return {"success": False, "message": "Defect not found or not New status"}

        # Verify that the field is required
        if not all([severity, priority, backlog_item_id]):
            return {"success": False, "message": "Severity, Priority and Backlog Item are required"}

        # Update defect information
        defect.severity = severity
        defect.priority = priority
        defect.status = 'Open'
        defect.approved_by = self.po_user
        defect.approved_at = timezone.now()
        defect.backlog_item_link = backlog_item_id
        defect.save()

        # Send a status change notification email
        send_status_change_notifications(defect, 'New', 'Open')

        return {
            "success": True,
            "message": "Report Approved and Marked as Open",
            "report_id": defect.id,
            "new_status": "Open"
        }

    # 4. Reject a New defect as invalid and notify tester
    def reject_defect_as_invalid(self, report_id, rejection_reason):
        if not self.product:
            return {"success": False, "message": "User is not a Product Owner"}

        if not rejection_reason or not str(rejection_reason).strip():
            return {"success": False, "message": "Rejection reason is required"}

        try:
            defect = DefectReport.objects.get(
                id=report_id,
                product=self.product,
                status='New'
            )
        except DefectReport.DoesNotExist:
            return {"success": False, "message": "Defect not found or not New status"}

        old_status = defect.status
        defect.status = 'Rejected'
        defect.rejection_reason = str(rejection_reason).strip()
        defect.rejected_by = self.po_user
        defect.rejected_at = timezone.now()
        defect.save()

        send_status_change_notifications(defect, old_status, 'Rejected')

        return {
            "success": True,
            "message": "Report Rejected as Invalid",
            "report_id": defect.id,
            "new_status": "Rejected",
            "rejection_reason": defect.rejection_reason,
        }

    # 5. Mark a New defect as duplicate of an existing report and notify tester
    def mark_defect_as_duplicate(self, report_id, duplicate_of_report_id):
        if not self.product:
            return {"success": False, "message": "User is not a Product Owner"}

        if not duplicate_of_report_id:
            return {"success": False, "message": "duplicate_of_report_id is required"}

        try:
            duplicate_of_report_id = int(duplicate_of_report_id)
        except (TypeError, ValueError):
            return {"success": False, "message": "duplicate_of_report_id must be a valid integer"}

        if int(report_id) == int(duplicate_of_report_id):
            return {"success": False, "message": "A defect cannot be marked duplicate of itself"}

        try:
            defect = DefectReport.objects.get(
                id=report_id,
                product=self.product,
                status='New'
            )
        except DefectReport.DoesNotExist:
            return {"success": False, "message": "Defect not found or not New status"}

        try:
            original_defect = DefectReport.objects.get(
                id=duplicate_of_report_id,
                product=self.product,
            )
        except DefectReport.DoesNotExist:
            return {"success": False, "message": "Original defect for duplication not found"}

        if original_defect.status == 'New':
            return {"success": False, "message": "Duplicate target must already be opened"}

        old_status = defect.status
        defect.status = 'Duplicate'
        defect.duplicate_of = original_defect
        defect.save()

        send_status_change_notifications(defect, old_status, 'Duplicate')

        return {
            "success": True,
            "message": "Report Marked as Duplicate",
            "report_id": defect.id,
            "new_status": "Duplicate",
            "duplicate_of_report_id": original_defect.id,
        }

    # 6. Reopen a Fixed defect and return it to backlog
    def reopen_defect_report(self, report_id, reopen_reason):
        if not self.product:
            return {"success": False, "message": "User is not a Product Owner"}

        if not reopen_reason or not str(reopen_reason).strip():
            return {"success": False, "message": "Reopen reason is required"}

        try:
            defect = DefectReport.objects.get(
                id=report_id,
                product=self.product,
                status='Fixed'
            )
        except DefectReport.DoesNotExist:
            return {"success": False, "message": "Defect not found or not Fixed status"}

        old_status = defect.status
        defect.status = 'Reopened'
        defect.reopen_reason = str(reopen_reason).strip()
        defect.reopened_by = self.po_user
        defect.reopened_at = timezone.now()
        defect.assigned_developer = None
        defect.save()

        send_status_change_notifications(defect, old_status, 'Reopened')

        return {
            "success": True,
            "message": "Report Marked as Reopened",
            "report_id": defect.id,
            "new_status": "Reopened",
            "reopen_reason": defect.reopen_reason,
            "reopened_at": defect.reopened_at,
            "reopened_by": self.po_user.username,
        }

