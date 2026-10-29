"""Settings, form options, colour palettes and demo scenarios for MediGuide AI."""
import os

from dotenv import load_dotenv

load_dotenv()  # reads a local .env file if one exists (never committed)

APP_NAME = "MediGuide AI"
APP_ICON = "🩺"
TAGLINE = "Safety-first symptom guidance — educational only"

DEFAULT_MODEL = "gpt-4o-mini"
MODEL_OPTIONS = ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"]
LANGUAGES = ["English", "Urdu", "Hindi", "Arabic", "Spanish", "French", "German", "Turkish", "Bengali"]
RTL_LANGUAGES = {"Urdu", "Arabic"}  # shown right-to-left

CACHE_OPTIONS = ["In-memory", "SQLite", "Off"]
SQLITE_PATH = os.path.join("data", "mediguide_cache.db")

GENDERS = ["Female", "Male", "Other / prefer not to say"]
DURATIONS = ["Less than 1 day", "1-3 days", "4-7 days", "1-2 weeks", "More than 2 weeks", "More than 1 month"]
LONG_DURATIONS = {"4-7 days", "1-2 weeks", "More than 2 weeks", "More than 1 month"}

SYMPTOMS = [
    "Fever", "Cough", "Sore throat", "Runny nose", "Headache", "Chest pain", "Shortness of breath",
    "Nausea", "Vomiting", "Diarrhea", "Abdominal pain", "Fatigue", "Dizziness", "Rash", "Muscle aches",
    "Joint pain", "Loss of taste or smell", "Back pain", "Palpitations", "Blurred vision", "Swelling",
    "Frequent urination", "Difficulty swallowing", "Confusion", "Sudden weakness or numbness",
    "Loss of consciousness", "Severe bleeding",
]

# Emergency numbers are only a convenience; the user should always check their local number.
EMERGENCY_NUMBERS = {
    "Pakistan": "1122 (Rescue) or 115", "USA / Canada": "911", "United Kingdom": "999",
    "European Union": "112", "India": "112", "UAE": "998 / 999", "Saudi Arabia": "997", "Other": "your local emergency number",
}

# accent colours (c1, c2, c3) — light/dark base is handled in theme.py
ACCENTS = {
    "Teal Care": ("#14b8a6", "#38bdf8", "#a78bfa"),
    "Ocean": ("#3b82f6", "#06b6d4", "#8b5cf6"),
    "Rose": ("#f43f5e", "#fb923c", "#c084fc"),
    "Emerald": ("#10b981", "#a3e635", "#22d3ee"),
    "Violet": ("#8b5cf6", "#ec4899", "#38bdf8"),
}

URGENCY_COLORS = {"LOW": "#22c55e", "MEDIUM": "#f59e0b", "HIGH": "#f97316", "EMERGENCY": "#dc2626"}

DISCLAIMER = (
    "MediGuide AI is an EDUCATIONAL AI prototype. It is NOT a doctor, does NOT give a diagnosis, and is NOT a "
    "replacement for professional medical care or emergency services. Always consult a qualified healthcare "
    "professional, and seek emergency help immediately in urgent situations."
)

SCENARIOS = {
    "1. Mild cold (25, runny nose + sore throat)": dict(
        age="25", gender="Female", symptoms=["Runny nose", "Sore throat"], duration="1-3 days", severity=2,
        conds="", meds="", notes="", language="English"),
    "2. Fever + cough (40, 4-7 days)": dict(
        age="40", gender="Male", symptoms=["Fever", "Cough"], duration="4-7 days", severity=6,
        conds="", meds="Paracetamol as needed", notes="Tired and sweating at night.", language="English"),
    "3. Severe chest pain + breathlessness": dict(
        age="52", gender="Male", symptoms=["Chest pain", "Shortness of breath"], duration="Less than 1 day",
        severity=9, conds="High blood pressure", meds="", notes="Pain started suddenly.", language="English"),
    "4. Same as #2 but answer in Urdu": dict(
        age="40", gender="Male", symptoms=["Fever", "Cough"], duration="4-7 days", severity=6,
        conds="", meds="", notes="", language="Urdu"),
}


def env_api_key() -> str:
    """Key from .env — only offered in the UI if MEDIGUIDE_ALLOW_ENV_KEY=1 (local use)."""
    if os.getenv("MEDIGUIDE_ALLOW_ENV_KEY", "0") != "1":
        return ""
    return os.getenv("OPENAI_API_KEY", "").strip()
