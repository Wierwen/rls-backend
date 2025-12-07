from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from django.utils.timezone import now

from .questionnaire_loader import list_questionnaire_slugs, load_all_questionnaires, load_questionnaire
from .firely_client import upload_questionnaire, upload_questionnaire_response, get_patient_responses

@api_view(["GET"])
def list_questionnaires(request):
    """
    Gibt alle dynamisch verfügbaren Fragebögen zurück
    (slug, title, description, status).
    """
    return Response(load_all_questionnaires())


@api_view(["GET"])
def questionnaire_detail(request, slug):
    try:
        data = load_questionnaire(slug)
        return Response(data)
    except FileNotFoundError:
        return Response(
            {"detail": f"Questionnaire '{slug}' nicht gefunden."},
            status=status.HTTP_404_NOT_FOUND
        )

def calculate_score_from_response(questionnaire_slug: str, fhir_response: dict) -> int:
    """
    Sehr vereinfachte Score-Berechnung:
    Erwartet im fhir_response:
    {
      "item": [
        { "linkId": "...", "answer": [ { "valueCoding": { "code": "3" } } ] },
        ...
      ]
    }
    Summiert alle Codes als Integer.
    """
    total = 0
    items = fhir_response.get("item", [])
    for item in items:
        answers = item.get("answer", [])
        if not answers:
            continue
        coding = answers[0].get("valueCoding")
        if not coding:
            continue
        code_str = coding.get("code")
        try:
            total += int(code_str)
        except (TypeError, ValueError):
            continue
    return total


@api_view(["POST"])
def submit_questionnaire_response(request, slug: str):
    """
    Nimmt Antworten zu einem Fragebogen entgegen, berechnet den Score
    und gibt ihn zurück (ohne Speicherung in der DB).

    POST /api/questionnaires/<slug>/responses/
    """
    try:
        load_questionnaire(slug)
    except FileNotFoundError:
        return Response(
            {"detail": f"Questionnaire with slug '{slug}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    
    patient_id = request.data.get("patient_id")
    answers = request.data.get("fhir_response")

    if not patient_id or not answers:
        return Response(
            {"detail": "patient_id und fhir_response sind erforderlich."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    total_score = calculate_score_from_response(slug, answers)
    interpretation = interpret_score(slug, total_score)
    fhir_response = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "authored": now().isoformat(),
        "questionnaire": f"Questionnaire/{slug}",
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "item": answers.get("item", [])
    }
    try:
        firely_result = upload_questionnaire_response(fhir_response)
    except Exception as e:
        return Response(
            {"detail": "Fehler beim Speichern in Firely", "error": str(e)},
            status=500,
        )


    return Response(
        {
            "questionnaire_slug": slug,
            "patient_id": patient_id,
            "total_score": total_score,
            "interpretation": interpretation,
            "fhir_response": fhir_response,
        },
        status=status.HTTP_201_CREATED,
    )
##TEST
@api_view(["POST"])
def upload_questionnaire_to_firely(request, slug: str):
    """
    Lädt ein Questionnaire-Template aus JSON in den Firely Server hoch.
    Testfunktion.
    """

    try:
        questionnaire_json = load_questionnaire(slug)
    except FileNotFoundError:
        return Response({"detail": "Questionnaire nicht gefunden."}, status=404)

    try:
        result = upload_questionnaire(questionnaire_json)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    return Response(result)
##TEST END

def interpret_score(questionnaire_slug: str, total_score: int) -> str:
    """
    Gibt eine einfache verbale Interpretation des Scores zurück.
    Die Schwellenwerte sind beispielhaft und können an Leitlinien angepasst werden.
    """
    if questionnaire_slug == "mental_health":
        # Bereich 0–40
        if total_score <= 10:
            return "keine oder minimale psychische Belastung"
        elif total_score <= 20:
            return "leichte psychische Belastung"
        elif total_score <= 30:
            return "moderate psychische Belastung"
        else:
            return "schwere psychische Belastung"

    if questionnaire_slug == "rls_schlafscore":
        # Bereich 0–30
        if total_score <= 5:
            return "kaum schlafbezogene Beeinträchtigung durch RLS"
        elif total_score <= 15:
            return "leichte bis moderate Beeinträchtigung"
        elif total_score <= 25:
            return "deutliche schlafbezogene Beeinträchtigung"
        else:
            return "schwere schlafbezogene Beeinträchtigung"

    return "keine Interpretation verfügbar"

@api_view(["GET"])
def get_patient_questionnaire_responses(request, patient_id: str):
    """
    Holt alle QuestionnaireResponses für einen Patienten aus Firely,
    berechnet Score & Interpretation und gibt sie sortiert zurück.
    """
    try:
        bundle = get_patient_responses(patient_id)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

    entries = bundle.get("entry", [])

    results = []
    for item in entries:
        res = item.get("resource")
        if not res:
            continue

        questionnaire = res.get("questionnaire")
        authored = res.get("authored")
        
        if questionnaire:
            slug = questionnaire.split("/")[-1]
            score = calculate_score_from_response(slug, res)
            interpretation = interpret_score(slug, score)
        else:
            slug = None
            score = None
            interpretation = None

        results.append({
            "questionnaire": slug,
            "score": score,
            "interpretation": interpretation,
            "authored": authored,
            "raw": res
        })

    # nach Datum sortieren
    results.sort(key=lambda x: x["authored"])

    return Response({
        "patient_id": patient_id,
        "responses": results
    })
