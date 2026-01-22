from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User

from accounts.permissions import IsPatient, IsPractitioner
from .models import PractitionerPatient, PatientConsent
from .serializers import (
    MeSerializer,
    PatientListSerializer,
    PractitionerListSerializer,
    PatientDetailSerializer,
)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPatient])
def me(request):
    serializer = MeSerializer(request.user)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPractitioner])
def list_patients(request):
    # 1) alle zugeordneten Patienten des Practitioners
    patient_ids = PractitionerPatient.objects.filter(
        practitioner=request.user
    ).values_list("patient_id", flat=True)

    # 2) nur Patienten, die zusätzlich Consent erteilt haben
    consented_patient_ids = PatientConsent.objects.filter(
        practitioner=request.user,
        status=PatientConsent.Status.GRANTED,
        patient_id__in=patient_ids,
    ).values_list("patient_id", flat=True)

    patients = User.objects.filter(
        id__in=consented_patient_ids,
        groups__name="patients",
    )

    serializer = PatientListSerializer(patients, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPractitioner])
def patient_detail(request, patient_id):
    # 1) prüfen: ist der Patient dem Practitioner zugeordnet?
    is_assigned = PractitionerPatient.objects.filter(
        practitioner=request.user,
        patient_id=patient_id,
    ).exists()

    if not is_assigned:
        return Response(
            {"detail": "Not allowed to access this patient"},
            status=403,
        )

    # 1b) prüfen: hat der Patient Consent erteilt?
    has_consent = PatientConsent.objects.filter(
        practitioner=request.user,
        patient_id=patient_id,
        status=PatientConsent.Status.GRANTED,
    ).exists()

    if not has_consent:
        return Response(
            {"detail": "No consent granted by patient"},
            status=403,
        )

    # 2) Patient laden
    try:
        patient = User.objects.get(id=patient_id, groups__name="patients")
    except User.DoesNotExist:
        return Response(
            {"detail": "Patient not found"},
            status=404,
        )

    # 3) Daten zurückgeben
    serializer = PatientDetailSerializer(patient)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPatient])
def my_practitioners(request):
    practitioner_ids = PractitionerPatient.objects.filter(
        patient=request.user
    ).values_list("practitioner_id", flat=True)

    practitioners = User.objects.filter(
        id__in=practitioner_ids,
        groups__name="practitioners",
    )

    serializer = PractitionerListSerializer(practitioners, many=True)
    return Response(serializer.data)
