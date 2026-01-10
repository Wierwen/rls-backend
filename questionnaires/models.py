from django.db import models

# Create your models here.
## Bisschen unnötig, wenn wir JSON und den Firly Client haben.


from django.core.exceptions import ValidationError

try:
    from fhir.resources.questionnaire import Questionnaire as FHIRQuestionnaire
except ImportError:
    FHIRQuestionnaire = None


class FHIRQuestionnaireModel(models.Model):
    """
    Speichert einen FHIR Questionnaire als JSON.
    """

    # Technical ID, z. B. 'rls-schlafscore'
    slug = models.SlugField(primary_key=True, max_length=100)

    # Lesbarer Titel
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # FHIR-Questionnaire-JSON
    fhir_resource = models.JSONField()

    # z. B. 'RLS' für Restless Legs
    condition_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="z. B. 'RLS' für Restless-Legs-Patienten"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        """
        Validiert optional gegen FHIR-Schema.
        """
        if FHIRQuestionnaire is not None:
            try:
                FHIRQuestionnaire.parse_obj(self.fhir_resource)
            except Exception as e:
                raise ValidationError({"fhir_resource": f"Invalid FHIR Questionnaire: {e}"})

    def __str__(self):
        return f"{self.slug} – {self.title}"

class QuestionnaireResponseModel(models.Model):
    """
    Speichert Antworten eines Patienten auf einen FHIR-Questionnaire.
    Vereinfachtes FHIR QuestionnaireResponse + Gesamt-Score.
    """

    id = models.AutoField(primary_key=True)

    # Welcher Fragebogen?
    questionnaire = models.ForeignKey(
        FHIRQuestionnaireModel,
        on_delete=models.CASCADE,
        related_name="responses",
    )

    # Patient – für den Anfang einfach eine ID als String
    patient_id = models.CharField(max_length=100)

    # Rohantworten im (vereinfachten) FHIR-Format
    # z. B.:
    # {
    #   "item": [
    #       {"linkId": "stimmung", "answer": [{"valueCoding": {"code": "5"}}]},
    #       ...
    #   ]
    # }
    fhir_response = models.JSONField()

    # Berechneter Gesamt-Score (z.B. 0–40 oder 0–30)
    total_score = models.IntegerField()
    

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.questionnaire.slug} – {self.patient_id} – Score {self.total_score}"
