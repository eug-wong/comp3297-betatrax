# services.py
from django.utils import timezone
from django.core.mail import send_mail
from .models import DefectReport, Product

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
        self._send_status_notification(defect)

        return {
            "success": True,
            "message": "Report Approved and Marked as Open",
            "report_id": defect.id,
            "new_status": "Open"
        }

    # Internal: Send notification letters
    def _send_status_notification(self, defect):
        if not defect.tester_email:
            return

        subject = f"BetaTrax: Defect Report {defect.id} Status Updated"
        message = f"""
        Defect Report ID: {defect.id}
        Title: {defect.title}
        Old Status: New
        New Status: Open
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
            # Failed mail delivery does not block the process
            pass
