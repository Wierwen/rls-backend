from django.contrib import admin
from .models import Patient, PractitionerPatient, PatientConsent


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "pseudonym", "created_at")
    search_fields = ("user__username", "pseudonym")


@admin.register(PractitionerPatient)
class PractitionerPatientAdmin(admin.ModelAdmin):
    list_display = ("id", "practitioner", "patient", "created_at")
    search_fields = ("practitioner__username", "patient__username")
    list_filter = ("created_at",)


@admin.register(PatientConsent)
class PatientConsentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "practitioner", "status", "granted_at", "revoked_at", "updated_at")
    search_fields = ("patient__username", "practitioner__username")
    list_filter = ("status", "updated_at")
