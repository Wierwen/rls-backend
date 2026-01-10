# questionnaires/views.py

import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now

from .questionnaire_loader import load_all_questionnaires, load_questionnaire
from .firely_client import (
    upload_questionnaire,
    upload_questionnaire_response,
    get_patient_responses,
)


# ----------------------------
# Helpers
# ----------------------------

def normalize_slug(slug: str) -> str:
    """
    Normalisiert Slugs robust:
    - strip / lower
    - "_" -> "-"
    - CR/LF entfernen
    - führende/abschließende "/" entfernen
    - Sonderzeichen entfernen (nur [a-z0-9-] bleibt)
    """
    s = (slug or "").strip().lower()
    s = s.replace("_", "-")
    s = s.replace("\n", "").replace("\r", "")
    s = s.strip("/")
    s = re.sub(r"[^a-z0-9\-]", "", s)
    return s


def slug_key(slug: str) -> str:
    """
    Für stabile Erkennung unabhängig von Bindestrichen:
    "rls-6" -> "rls6"
    """
    return normalize_slug(slug).replace("-", "")


def answer_to_int(answer_obj: dict):
    """
    Unterstützt:
    - {"valueInteger": 3}
    - {"valueCoding": {"code": "3"}}
    """
    if not isinstance(answer_obj, dict):
        return None

    if "valueInteger" in answer_obj:
        try:
            return int(answer_obj["valueInteger"])
        except (TypeError, ValueError):
            return None

    coding = answer_obj.get("valueCoding")
    if isinstance(coding, dict) and "code" in coding:
        try:
            return int(coding["code"])
        except (TypeError, ValueError):
            return None

    return None


def calculate_total_score_from_response(qr: dict) -> int:
    """
    Summiert alle numerischen Antworten aus einer QuestionnaireResponse.
    """
    total = 0
    for item in (qr.get("item") or []):
        answers = item.get("answer") or []
        if not answers:
            continue
        v = answer_to_int(answers[0])
        if v is not None:
            total += v
    return total


def score_rls6(qr: dict) -> dict:
    """
    RLS-6 domain-basiert (kein Gesamtscore):
    - Sleep quality: Items 1 + 6
    - Nighttime RLS: Items 2 + 3
    - Daytime relaxation: Item 4
    - Control (activity/mimics): Item 5
    """
    values = {}

    for item in (qr.get("item") or []):
        link_id = item.get("linkId")
        if not link_id:
            continue

        answers = item.get("answer") or []
        if not answers:
            continue

        v = answer_to_int(answers[0])
        if v is not None:
            values[str(link_id)] = v

    sleep_quality = (values["1"] + values["6"]) if "1" in values and "6" in values else None
    nighttime = (values["2"] + values["3"]) if "2" in values and "3" in values else None
    daytime_relax = values.get("4")
    control_activity = values.get("5")

    return {
        "type": "rls6_domains",
        "sleep_quality_items_1_6": sleep_quality,
        "nighttime_items_2_3": nighttime,
        "daytime_relaxation_item_4": daytime_relax,
        "control_activity_item_5": control_activity,
        "raw": values,
    }

def score_mhi5(qr: dict) -> dict:
    """
    MHI-5 Gesamtscore (0-100):
    - Items a-e
    - Umkehrung bei c und e

    """
    values = {}

    for item in (qr.get("item") or[]):
        link_id = item.get("linkId")
        answers = item.get("answer"), []
        if not link_id:
            continue
        a0 = answers[0]

        if "valueInteger" in a0:
            values[link_id]=int(a0["valueInteger"])
        elif "valueCoding" in a0 and "code" in a0["valueCoding"]:
            values[link_id]=int(a0["valueCoding"]["code"])    

        #direct
        a = values.get("a")
        b = values.get("b")
        d = values.get("d")    
        #inversion
        c= 7 - values.get("c") if "c" in values else None
        e= 7 - values.get("e") if "e" in values else None

        raw_sum = sum(v for v in [a,b,c,d,e] if v is not None)

        transformed = None
        if raw_sum  is not None:
            transformed= round(((raw_sum - 5) / 20) * 100,1)

            return {
                "type": "mhi5",
                "total_score": transformed,
                "raw_items": values,
                "raw_sum":raw_sum
            }
        
                 

def interpret_score(questionnaire_slug: str, total_score: int) -> str:
    """
    Interpretation nur für Scores, die einen Gesamtscore haben (z.B. IRLS).
    """
    key = slug_key(questionnaire_slug)

    # IRLS: 0–40
    if key == "irls":
        if total_score == 0:
            return "kein RLS"
        if total_score <= 10:
            return "mildes RLS"
        if total_score <= 20:
            return "mittelgradiges RLS"
        if total_score <= 30:
            return "schweres RLS"
        return "sehr schweres RLS"

    return "keine Interpretation verfügbar"


# ----------------------------
# Endpoints
# ----------------------------

@api_view(["GET"])
def list_questionnaires(request):
    return Response(load_all_questionnaires())


@api_view(["GET"])
def questionnaire_detail(request, slug):
    try:
        data = load_questionnaire(slug)
        return Response(data)
    except FileNotFoundError:
        return Response(
            {"detail": f"Questionnaire '{slug}' nicht gefunden."},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
def submit_questionnaire_response(request, slug: str):
    """
    POST /api/questionnaires/<slug>/responses/

    Body:
    {
      "patient_id": "123",
      "fhir_response": {
        "item": [
          {"linkId":"1","answer":[{"valueCoding":{"code":"2"}}]},
          ...
        ]
      }
    }
    """
    # Questionnaire existiert?
    try:
        load_questionnaire(slug)
    except FileNotFoundError:
        return Response(
            {"detail": f"Questionnaire with slug '{slug}' not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    patient_id = request.data.get("patient_id")
    payload = request.data.get("fhir_response")

    if not patient_id or not payload:
        return Response(
            {"detail": "patient_id und fhir_response sind erforderlich."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # FHIR QuestionnaireResponse (R5)
    qr = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "authored": now().isoformat(),
        "questionnaire": f"Questionnaire/{slug}",
        "subject": {"reference": f"Patient/{patient_id}"},
        "item": payload.get("item", []),
    }

    key = slug_key(slug)

    # RLS-6 -> domains
    if key == "rls6":
        computed = score_rls6(qr)
        total_score = None
        interpretation = (
            "RLS-6 wird domain-basiert ausgewertet (kein Gesamtscore). "
            f"Sleep(1+6)={computed.get('sleep_quality_items_1_6')}, "
            f"Night(2+3)={computed.get('nighttime_items_2_3')}, "
            f"DayRelax(4)={computed.get('daytime_relaxation_item_4')}, "
            f"Control(5)={computed.get('control_activity_item_5')}"
        )
    else:
        # IRLS -> totalscore
        total_score = calculate_total_score_from_response(qr)
        interpretation = interpret_score(slug, total_score)
        computed = {"type": "total_score", "total_score": total_score}

    # Speichern in Firely
    try:
        upload_questionnaire_response(qr)
    except Exception as e:
        return Response(
            {"detail": "Fehler beim Speichern in Firely", "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {
            "questionnaire_slug": slug,
            "patient_id": patient_id,
            "total_score": total_score,
            "interpretation": interpretation,
            "fhir_response": qr,
            "computed": computed,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def upload_questionnaire_to_firely(request, slug: str):
    """
    POST /api/questionnaires/<slug>/upload/
    """
    try:
        questionnaire_json = load_questionnaire(slug)
    except FileNotFoundError:
        return Response(
            {"detail": "Questionnaire nicht gefunden."},
            status=status.HTTP_404_NOT_FOUND,
        )
    except ValueError as e:
        return Response(
            {"detail": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        result = upload_questionnaire(questionnaire_json)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(result)


@api_view(["GET"])
def get_patient_questionnaire_responses(request, patient_id: str):
    """
    GET /api/patients/<patient_id>/responses/
    """
    try:
        bundle = get_patient_responses(patient_id)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    entries = bundle.get("entry") or []
    results = []

    for entry in entries:
        res = entry.get("resource")
        if not res:
            continue

        questionnaire_ref = res.get("questionnaire")  # "Questionnaire/RLS-6"
        authored = res.get("authored")

        qslug = None
        score = None
        interpretation = None
        computed = None

        if questionnaire_ref:
            qslug = questionnaire_ref.split("/")[-1]
            qkey = slug_key(qslug)

            if qkey == "rls6":
                computed = score_rls6(res)
                score = None
                interpretation = "RLS-6 wird domain-basiert ausgewertet (kein Gesamtscore)."
            else:
                score = calculate_total_score_from_response(res)
                interpretation = interpret_score(qslug, score)
                computed = {"type": "total_score", "total_score": score}

        results.append(
            {
                "questionnaire": qslug,
                "score": score,
                "computed": computed,
                "interpretation": interpretation,
                "authored": authored,
                "raw": res,
            }
        )

    results.sort(key=lambda x: x["authored"] or "")
    return Response({"patient_id": patient_id, "responses": results})
