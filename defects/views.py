from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.core.mail import send_mail

from .models import DefectReport
from .serializers import DefectReportSerializer


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
