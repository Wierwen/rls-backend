from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework import status

from accounts.permissions import IsPractitioner
from patients.models import PractitionerPatient

@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPractitioner])
def me(request):
    return Response({
        "id": request.user.id,
        "username": request.user.username,
        "email": request.user.email,
    })
@api_view(["POST"])
@permission_classes([IsAuthenticated, IsPractitioner])
def assign_patient(request):
    patient_id = request.data.get("patient_id")

    if patient_id is None:
        return Response(
            {"detail": "patient_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Patient muss existieren und in Gruppe 'patients' sein
    try:
        patient = User.objects.get(id=patient_id, groups__name="patients")
    except User.DoesNotExist:
        return Response(
            {"detail": "Patient not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # idempotent: doppelte Zuordnung verhindern
    link, created = PractitionerPatient.objects.get_or_create(
        practitioner=request.user,
        patient=patient,
    )

    return Response(
        {
            "assigned": True,
            "created": created,
            "practitioner_id": request.user.id,
            "patient_id": patient.id,
        },
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
    )

@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsPractitioner])
def unassign_patient(request):
    patient_id = request.data.get("patient_id")

    if patient_id is None:
        return Response(
            {"detail": "patient_id is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    deleted_count, _ = PractitionerPatient.objects.filter(
        practitioner=request.user,
        patient_id=patient_id,
    ).delete()

    return Response(
        {
            "deleted": deleted_count > 0,
            "patient_id": int(patient_id),
        },
        status=status.HTTP_200_OK,
    )

