from django.shortcuts import render

import csv
from django.http import HttpResponse
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import IsPractitioner
from patients.models import PractitionerPatient, Patient


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsPractitioner])
def export_assigned_patients_csv(request):
    # IDs der Patienten, die dem Practitioner zugeordnet sind
    patient_ids = PractitionerPatient.objects.filter(
        practitioner=request.user
    ).values_list("patient_id", flat=True)

    users = User.objects.filter(id__in=patient_ids).order_by("id")

    # Pseudonyme optional mappen (falls Patient-Profil existiert)
    pseudonym_by_user_id = {
        p.user_id: p.pseudonym
        for p in Patient.objects.filter(user_id__in=patient_ids)
    }

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="patients.csv"'

    writer = csv.writer(response)
    writer.writerow(["patient_id", "pseudonym", "username", "email"])

    for u in users:
        writer.writerow([u.id, pseudonym_by_user_id.get(u.id, ""), u.username, u.email])

    return response
