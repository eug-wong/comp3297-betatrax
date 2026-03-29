from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .services import ProductOwnerService

# API: List all New defect reports for PO (UC002)
class PO_NewDefectList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        po_service = ProductOwnerService(request.user)
        if not po_service.product:
            return Response({"error": "User is not a Product Owner"}, status=403)

        defects = po_service.get_new_defect_list()

        data = [{
            "report_id": d.id,
            "title": d.title,
            "tester_id": d.tester_id,
            "submitted_at": d.created_at,
            "status": d.status
        } for d in defects]

        return Response(data)

# API: Get full details of one defect report
class PO_DefectDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, defect_id):
        po_service = ProductOwnerService(request.user)
        if not po_service.product:
            return Response({"error": "User is not a Product Owner"}, status=403)

        defect = po_service.get_defect_detail(defect_id)

        if not defect:
            return Response({"error": "Defect not found"}, status=404)

        return Response({
            "report_id": defect.id,
            "product": defect.product.name,
            "title": defect.title,
            "description": defect.description,
            "reproduction_steps": defect.steps_to_reproduce,
            "tester_id": defect.tester_id,
            "tester_email": defect.tester_email,
            "status": defect.status,
            "submitted_at": defect.created_at
        })

# API: Approve defect and update status to Open (UC002 main function)
class PO_ApproveDefect(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, defect_id):
        po_service = ProductOwnerService(request.user)
        if not po_service.product:
            return Response({"error": "User is not a Product Owner"}, status=403)

        result = po_service.accept_and_approve_defect(
            report_id=defect_id,
            severity=request.data.get('severity'),
            priority=request.data.get('priority'),
            backlog_item_id=request.data.get('backlog_item_id')
        )

        if result["success"]:
            return Response(result)
        return Response(result, status=400)
