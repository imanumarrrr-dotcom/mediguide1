"""Helpers: age parsing, rule-based safety pre-check, SAFE JSON parsing, fallback and report export."""
import json
import re
from datetime import datetime

from config import DISCLAIMER, LONG_DURATIONS

LEVELS = ["LOW", "MEDIUM", "HIGH", "EMERGENCY"]


def max_urgency(a: str, b: str) -> str:
    """Return the more urgent of two levels (the AI can never lower the Python safety floor)."""
    return LEVELS[max(LEVELS.index(a) if a in LEVELS else 0, LEVELS.index(b) if b in LEVELS else 0)]


def parse_age(text: str):
    """Return (ok, age_int, message). Age comes from a text_input so it must be validated."""
    text = (text or "").strip()
    if not text.isdigit() or not 0 <= int(text) <= 120:
        return False, None, "Please enter a valid age as a whole number between 0 and 120."
    return True, int(text), ""


def crisis_check(*texts: str) -> bool:
    """True if the user's own words hint at self-harm (shows a supportive message)."""
    blob = " ".join(texts).lower()
    return any(k in blob for k in ("suicid", "kill myself", "end my life", "self-harm", "self harm", "hurt myself"))


def rule_urgency(patient: dict) -> dict:
    """Deterministic red-flag screen. It sets a MINIMUM urgency; the AI may only raise it."""
    text = " ".join(patient["symptoms"]).lower()
    has = lambda *words: any(w in text for w in words)  # noqa: E731
    sev, age, dur = patient["severity"], patient["age"], patient["duration"]
    chest, breath = has("chest pain", "chest tight"), has("shortness of breath", "breathless", "trouble breathing")
    found = []  # (level_index, reason)
    if has("unconscious", "faint", "loss of consciousness", "severe bleeding", "heavy bleeding", "numbness",
           "weakness", "slurred", "can't speak"):
        found.append((3, "possible stroke / bleeding / fainting warning sign"))
    if chest and breath:
        found.append((3, "chest pain together with shortness of breath"))
    if (chest or breath) and sev >= 8:
        found.append((3, "severe chest pain or breathing difficulty"))
    if chest or breath:
        found.append((2, "chest pain or breathing difficulty needs prompt assessment"))
    if has("confusion") or sev >= 8:
        found.append((2, "confusion or very high severity"))
    if has("fever") and (age <= 2 or age >= 65):
        found.append((2, "fever in a very young or older person"))
    if has("fever") and dur in LONG_DURATIONS:
        found.append((1, "fever lasting several days"))
    if sev >= 5 or dur in {"More than 2 weeks", "More than 1 month"} or len(patient["symptoms"]) >= 4:
        found.append((1, "moderate severity, long duration or many symptoms"))
    top = max((lvl for lvl, _ in found), default=0)
    return {"level": LEVELS[top], "reasons": [r for lvl, r in found if lvl == top]}


# ---------------------------------------------------------------- JSON parsing
def extract_json(text: str):
    """Strip ```json fences / chatter and parse the JSON object inside."""
    text = re.sub(r"```(?:json)?", "", text or "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("No JSON object found in the model reply.")
    return json.loads(text[start:end + 1])


def _as_list(value) -> list:
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(v) for v in value] if isinstance(value, list) else []


def validate_assessment(data: dict, rule_level: str) -> dict:
    """Coerce parsed JSON into the exact schema and apply the Python safety floor."""
    conds = []
    rows = data.get("possible_conditions")
    for row in rows if isinstance(rows, list) else []:
        if isinstance(row, dict):
            conds.append({"name": str(row.get("name", "")), "reason": str(row.get("reason", ""))})
        elif isinstance(row, str):
            conds.append({"name": row, "reason": ""})
    ai_level = str(data.get("urgency_level", "")).strip().upper()
    ai_level = ai_level if ai_level in LEVELS else rule_level
    return {
        "summary": str(data.get("summary", "")).strip() or "No summary returned.",
        "possible_conditions": conds, "ai_urgency": ai_level, "urgency_level": max_urgency(ai_level, rule_level),
        "recommended_next_steps": _as_list(data.get("recommended_next_steps")),
        "questions_for_doctor": _as_list(data.get("questions_for_doctor")),
        "warning_signs": _as_list(data.get("warning_signs")),
    }


def fallback_assessment(patient: dict, rule: dict) -> dict:
    """Rule-based guidance shown when the AI reply is unusable (the app never crashes)."""
    lvl = rule["level"]
    steps = {"EMERGENCY": ["Call your local emergency number or go to the nearest emergency room NOW.",
                           "Do not drive yourself; ask someone to stay with you."],
             "HIGH": ["Contact a doctor or urgent-care service today.", "Do not wait for symptoms to pass on their own."],
             "MEDIUM": ["Book an appointment with a doctor in the next few days.", "Rest, drink fluids and track symptoms."],
             "LOW": ["Rest, drink fluids and monitor your symptoms.", "See a doctor if things get worse or last long."]}[lvl]
    return {
        "summary": f"Rule-based summary: {', '.join(patient['symptoms'])} for {patient['duration']} (severity {patient['severity']}/10).",
        "possible_conditions": [], "ai_urgency": lvl, "urgency_level": lvl, "recommended_next_steps": steps,
        "questions_for_doctor": ["What could be causing my symptoms?", "Which tests (if any) do I need?",
                                 "When should I come back or seek urgent care?"],
        "warning_signs": ["Trouble breathing", "Chest pain or pressure", "Fainting or confusion", "Symptoms rapidly getting worse"],
    }


def parse_assessment(raw: str, patient: dict, rule: dict):
    """Return (assessment, warning_or_None). Never raises."""
    try:
        return validate_assessment(extract_json(raw), rule["level"]), None
    except Exception as exc:
        return fallback_assessment(patient, rule), f"The AI reply was not valid JSON ({exc}). Showing rule-based guidance."


def report_markdown(patient: dict, a: dict, narrative: str) -> str:
    L = [f"# MediGuide AI — Guidance Report ({datetime.now():%Y-%m-%d %H:%M})", "", f"> {DISCLAIMER}", "",
         f"**Age:** {patient['age']} · **Gender:** {patient['gender']} · **Duration:** {patient['duration']} · "
         f"**Severity:** {patient['severity']}/10", f"**Symptoms:** {', '.join(patient['symptoms'])}", "",
         f"## Urgency: {a['urgency_level']}", "", "## Summary", a["summary"], "", "## Possible conditions (education only)"]
    L += [f"- **{c['name']}** — {c['reason']}" for c in a["possible_conditions"]]
    for title, key in [("Recommended next steps", "recommended_next_steps"),
                       ("Questions for your doctor", "questions_for_doctor"), ("Warning signs", "warning_signs")]:
        L += ["", f"## {title}"] + [f"- {x}" for x in a[key]]
    if narrative:
        L += ["", "## Guidance note", narrative]
    return "\n".join(L)
