from rest_framework import serializers
from .models import FHIRQuestionnaireModel
from .models import FHIRQuestionnaireModel, QuestionnaireResponseModel

## Bisschen unnötig, wenn wir JSON und den Firly Client haben.

class FHIRQuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = FHIRQuestionnaireModel
        fields = [
            "slug",
            "title",
            "description",
            "condition_code",
            "fhir_resource",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

class QuestionnaireResponseSerializer(serializers.ModelSerializer):
    questionnaire_slug = serializers.SlugRelatedField(
        source="questionnaire",
        slug_field="slug",
        queryset=FHIRQuestionnaireModel.objects.all(),
        write_only=True,
    )

    class Meta:
        model = QuestionnaireResponseModel
        fields = [
            "id",
            "questionnaire_slug",
            "patient_id",
            "fhir_response",
            "total_score",
            "created_at",
        ]
        read_only_fields = ["id", "total_score", "created_at"]