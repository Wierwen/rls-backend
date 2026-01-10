import json
from pathlib import Path

BASE = Path(__file__).resolve().parent / "questionnaires_json"

def load_questionnaire(slug: str):
    file_path = BASE / f"{slug}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"{slug}.json nicht gefunden.")

    # Read as text first so we can produce better errors (and tolerate UTF-8 BOM).
    text = file_path.read_text(encoding="utf-8-sig")
    if not text.strip():
        raise ValueError(f"{file_path.name} ist leer oder enthält nur Whitespaces.")

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Ungültiges JSON in {file_path.name}: {e.msg} (line {e.lineno} col {e.colno})"
        ) from e

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