from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from patients.models import Patient, PatientConsent
from patients.serializers import PatientConsentSerializer, ConsentActionSerializer


def _get_patient_user(request):
    """
    Patient ist bei euch ein User mit Patient-Profil (patients.Patient).
    """
    patient_profile = get_object_or_404(Patient, user=request.user)
    return patient_profile.user


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_my_consents(request):
    patient_user = _get_patient_user(request)

    qs = PatientConsent.objects.filter(patient=patient_user).order_by("-updated_at")
    return Response(PatientConsentSerializer(qs, many=True).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def grant_consent(request):
    patient_user = _get_patient_user(request)

    s = ConsentActionSerializer(data=request.data)
    s.is_valid(raise_exception=True)

    practitioner_user = get_object_or_404(User, id=s.validated_data["practitioner_id"])

    consent, created = PatientConsent.objects.get_or_create(
        patient=patient_user,
        practitioner=practitioner_user,
        defaults={
            "status": PatientConsent.Status.GRANTED,
            "granted_at": timezone.now(),
        },
    )

    if not created:
        consent.grant()

    return Response(PatientConsentSerializer(consent).data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def revoke_consent(request):
    patient_user = _get_patient_user(request)

    s = ConsentActionSerializer(data=request.data)
    s.is_valid(raise_exception=True)

    practitioner_user = get_object_or_404(User, id=s.validated_data["practitioner_id"])

    consent = get_object_or_404(
        PatientConsent,
        patient=patient_user,
        practitioner=practitioner_user,
    )

    consent.revoke()
    return Response(PatientConsentSerializer(consent).data, status=status.HTTP_200_OK)

