from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from doctors.serializers import DoctorSerializer
from patients.models import Patient

from .models import PatientDoctorMapping
from .serializers import MappingSerializer


class MappingListCreateView(generics.ListCreateAPIView):
    serializer_class = MappingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only mappings of the logged-in user's own patients
        return PatientDoctorMapping.objects.filter(
            patient__owner=self.request.user
        ).select_related("patient", "doctor")


class PatientMappingView(APIView):
    """
    GET    /api/mappings/<patient_id>/ -> doctors assigned to that patient
    DELETE /api/mappings/<id>/         -> remove that mapping (by mapping id)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        patient = get_object_or_404(Patient, pk=pk, owner=request.user)
        mappings = PatientDoctorMapping.objects.filter(
            patient=patient
        ).select_related("doctor")

        doctors = []
        for mapping in mappings:
            data = dict(DoctorSerializer(mapping.doctor).data)
            data["mapping_id"] = mapping.id
            data["assigned_at"] = mapping.assigned_at
            doctors.append(data)

        return Response(
            {
                "patient_id": patient.id,
                "patient_name": patient.name,
                "doctors": doctors,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):
        mapping = get_object_or_404(
            PatientDoctorMapping, pk=pk, patient__owner=request.user
        )
        mapping.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
