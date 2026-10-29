"""Tests for the deterministic safety net and JSON parsing (no API key needed)."""
from src.utils import max_urgency, parse_age, parse_assessment, rule_urgency


def P(symptoms, sev, age=30, dur="1-3 days"):
    return dict(age=age, gender="Female", symptoms=symptoms, duration=dur, severity=sev,
                conditions="", medications="", notes="")


def test_scenarios():
    assert rule_urgency(P(["Runny nose", "Sore throat"], 2, 25))["level"] == "LOW"           # 1
    assert rule_urgency(P(["Fever", "Cough"], 6, 40, "4-7 days"))["level"] in ("MEDIUM", "HIGH")  # 2
    assert rule_urgency(P(["Chest pain", "Shortness of breath"], 9))["level"] == "EMERGENCY"  # 3
    assert rule_urgency(P(["severe bleeding"], 5))["level"] == "EMERGENCY"


def test_age_validation():
    assert parse_age("25")[0] and not parse_age("")[0] and not parse_age("abc")[0] and not parse_age("200")[0]


def test_ai_cannot_lower_urgency():
    rule = rule_urgency(P(["Chest pain", "Shortness of breath"], 9))
    a, warn = parse_assessment('```json\n{"urgency_level": "low", "summary": "x"}\n```', P([], 9), rule)
    assert warn is None and a["urgency_level"] == "EMERGENCY" and a["ai_urgency"] == "LOW"
    a, warn = parse_assessment("totally not json", P(["Fever"], 3), {"level": "MEDIUM", "reasons": []})
    assert warn and a["urgency_level"] == "MEDIUM" and max_urgency("LOW", "HIGH") == "HIGH"
