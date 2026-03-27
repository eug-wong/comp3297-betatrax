from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import DefectReport
from .serializers import ResolveDefectSerializer

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
