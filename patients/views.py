from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from accounts.permissions import IsPatient, IsPractitioner
from .serializers import MeSerializer, PatientListSerializer
from .models import PractitionerPatient
from .serializers import PractitionerListSerializer
from .serializers import PatientDetailSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPatient])
def me(request):
    serializer = MeSerializer(request.user)
    return Response(serializer.data)

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPractitioner])
def list_patients(request):
    patient_ids = PractitionerPatient.objects.filter(
        practitioner=request.user
    ).values_list("patient_id", flat=True)

    patients = User.objects.filter(id__in=patient_ids)
    serializer = PatientListSerializer(patients, many=True)
    return Response(serializer.data)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPractitioner])
def patient_detail(request, patient_id):
    # 1. prüfen: ist der Patient dem Practitioner zugeordnet?
    is_assigned = PractitionerPatient.objects.filter(
        practitioner=request.user,
        patient_id=patient_id,
    ).exists()

    if not is_assigned:
        return Response(
            {"detail": "Not allowed to access this patient"},
            status=403,
        )

    # 2. Patient laden
    try:
        patient = User.objects.get(id=patient_id, groups__name="patients")
    except User.DoesNotExist:
        return Response(
            {"detail": "Patient not found"},
            status=404,
        )

    # 3. Daten zurückgeben
    serializer = PatientDetailSerializer(patient)
    return Response(serializer.data)
@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPatient])
def my_practitioners(request):
    practitioner_ids = PractitionerPatient.objects.filter(
        patient=request.user
    ).values_list("practitioner_id", flat=True)

    practitioners = User.objects.filter(id__in=practitioner_ids)
    serializer = PractitionerListSerializer(practitioners, many=True)
    return Response(serializer.data)

