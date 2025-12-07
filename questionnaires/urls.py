from django.urls import path
from .views import (
    list_questionnaires,
    questionnaire_detail,
    submit_questionnaire_response,
    upload_questionnaire_to_firely,
    get_patient_questionnaire_responses
)

urlpatterns = [
    path("patients/<str:patient_id>/responses/", get_patient_questionnaire_responses),
    path("questionnaires/<slug:slug>/upload/", upload_questionnaire_to_firely),
    path("questionnaires/", list_questionnaires, name="questionnaire-list"),
    path("questionnaires/<slug:slug>/", questionnaire_detail, name="questionnaire-detail"),
    path(
        "questionnaires/<slug:slug>/responses/",
        submit_questionnaire_response,
        name="questionnaire-submit-response",
    ),
]


