from rest_framework import serializers

from patients.models import Patient

from .models import PatientDoctorMapping


class MappingSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)

    class Meta:
        model = PatientDoctorMapping
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "assigned_at",
        ]
        read_only_fields = ["id", "assigned_at"]
        # Duplicate check is done manually in validate() for a clearer message
        validators = []

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            # Only the user's own patients are valid choices
            fields["patient"].queryset = Patient.objects.filter(owner=request.user)
        return fields

    def validate(self, attrs):
        if PatientDoctorMapping.objects.filter(
            patient=attrs["patient"], doctor=attrs["doctor"]
        ).exists():
            raise serializers.ValidationError(
                "This doctor is already assigned to this patient."
            )
        return attrs
