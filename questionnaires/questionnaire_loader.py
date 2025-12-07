import json
from pathlib import Path

BASE = Path(__file__).resolve().parent / "questionnaires_json"

def load_questionnaire(slug: str):
    file_path = BASE / f"{slug}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"{slug}.json nicht gefunden.")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def list_questionnaire_slugs():
    return [
        p.stem
        for p in BASE.glob("*.json")
    ]


def load_all_questionnaires():
    questionnaires = []

    for slug in list_questionnaire_slugs():
        data = load_questionnaire(slug)
        questionnaires.append({
            "slug": slug,
            "title": data.get("title"),
            "description": data.get("description"),
            "status": data.get("status", "unknown"),
        })

    return questionnaires