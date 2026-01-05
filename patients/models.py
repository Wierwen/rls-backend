from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import secrets


def generate_pseudonym(prefix: str = "SL") -> str:
    # SL-00000 bis SL-99999
    return f"{prefix}-{secrets.randbelow(100000):05d}"


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="patient_profile")
    pseudonym = models.CharField(max_length=20, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pseudonym:
            # sehr seltene Kollisionen abfangen
            for _ in range(10):
                candidate = generate_pseudonym()
                if not Patient.objects.filter(pseudonym=candidate).exists():
                    self.pseudonym = candidate
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.pseudonym or f"Patient {self.pk}"
class PractitionerPatient(models.Model):
    practitioner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_patients",
        limit_choices_to={"groups__name": "practitioners"},
    )
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_practitioners",
        limit_choices_to={"groups__name": "patients"},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("practitioner", "patient")

    def __str__(self):
        return f"{self.practitioner.username} → {self.patient.username}"
