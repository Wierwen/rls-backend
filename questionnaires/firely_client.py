import requests
import logging

FHIR_BASE_URL = "http://localhost:4080"   # URL von Firely Server

logger = logging.getLogger(__name__)


def upload_questionnaire(questionnaire_json: dict) -> dict:
    """
    Lädt ein Questionnaire JSON in den Firely Server hoch.
    """
    url = f"{FHIR_BASE_URL}/Questionnaire"
    headers = {"Content-Type": "application/fhir+json"}

    response = requests.post(url, json=questionnaire_json, headers=headers)

    if response.status_code not in (200, 201):
        logger.error("Fehler beim Hochladen des Questionnaires: %s", response.text)
        raise Exception(f"Upload fehlgeschlagen: {response.status_code} – {response.text}")

    return response.json()


def upload_questionnaire_response(response_json: dict) -> dict:
    """
    Lädt eine QuestionnaireResponse an Firely.
    """
    url = f"{FHIR_BASE_URL}/QuestionnaireResponse"
    headers = {"Content-Type": "application/fhir+json"}

    response = requests.post(url, json=response_json, headers=headers)

    if response.status_code not in (200, 201):
        logger.error("Fehler beim Hochladen der QuestionnaireResponse: %s", response.text)
        raise Exception(f"Upload fehlgeschlagen: {response.status_code} – {response.text}")

    return response.json()


def get_resource(resource_type: str, resource_id: str) -> dict:
    """
    Holt eine Ressource vom Firely Server.
    z.B. get_resource("Questionnaire", "12345")
    """
    url = f"{FHIR_BASE_URL}/{resource_type}/{resource_id}"
    response = requests.get(url)

    if response.status_code != 200:
        logger.error("Fehler beim Abrufen der Ressource: %s", response.text)
        raise Exception(f"Abrufen fehlgeschlagen: {response.status_code} – {response.text}")

    return response.json()


def get_patient_responses(patient_id: str):
    """
    Holt alle QuestionnaireResponses aus Firely für einen Patienten.
    """
    url = f"{FHIR_BASE_URL}/QuestionnaireResponse"
    params = {"subject": f"Patient/{patient_id}"}
    headers = {"Accept": "application/fhir+json"}

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()