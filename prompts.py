"""Prompt engineering: system safety rules, PromptTemplate, ChatPromptTemplate and the JSON schema."""
import json

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate

# ---- System prompt: role + medical safety rules ----------------------------
SYSTEM_PROMPT = """You are MediGuide AI, an EDUCATIONAL medical-information assistant inside a classroom prototype.

NON-NEGOTIABLE SAFETY RULES:
- You are NOT a doctor. Never state or imply a confirmed diagnosis; "possible conditions" are for education only.
- Never prescribe medicines or doses. You may say general things like "ask a pharmacist or doctor".
- If symptoms could be serious (e.g. chest pain, trouble breathing, stroke signs, heavy bleeding, fainting,
  confusion, thoughts of self-harm), set urgency_level to HIGH or EMERGENCY and tell the user to seek emergency
  help immediately.
- Be calm, kind and clear; avoid causing panic. Always recommend consulting a qualified healthcare professional.
- Respect the Python safety pre-check: never go BELOW the urgency it reports.
Write all free-text values in {language}. Keep the JSON key names and the urgency_level word (LOW, MEDIUM, HIGH or
EMERGENCY) in English."""

# ---- Exact JSON schema from the assignment ---------------------------------
JSON_SCHEMA = {
    "summary": "",
    "possible_conditions": [{"name": "", "reason": ""}],
    "urgency_level": "",
    "recommended_next_steps": [],
    "questions_for_doctor": [],
    "warning_signs": [],
}
# braces doubled so LangChain does not read the schema as template variables
SCHEMA_TEXT = json.dumps(JSON_SCHEMA, indent=2).replace("{", "{{").replace("}", "}}")

JSON_RULES = f"""Return ONLY one valid JSON object (no markdown, no extra text) with exactly this schema:
{SCHEMA_TEXT}
Rules: urgency_level is exactly one of LOW, MEDIUM, HIGH, EMERGENCY. possible_conditions has 2-4 items for education
only (never a confirmed diagnosis). Each list has 3-5 short, practical strings."""

# ---- PromptTemplate (single string with the patient variables) --------------
PATIENT_TEMPLATE = """PATIENT INFORMATION:
- age: {age}
- gender: {gender}
- symptoms: {symptoms}
- duration: {duration}
- severity (1-10): {severity}
- existing conditions: {conditions}
- current medications: {medications}
- additional notes: {notes}

PYTHON SAFETY PRE-CHECK (rule-based): minimum urgency = {rule_urgency}. Reason: {rule_reasons}"""

PATIENT_VARIABLES = ["age", "gender", "symptoms", "duration", "severity", "conditions", "medications",
                     "notes", "rule_urgency", "rule_reasons"]
PATIENT_PROMPT = PromptTemplate(input_variables=PATIENT_VARIABLES, template=PATIENT_TEMPLATE)

# ---- ChatPromptTemplates (System + Human) -----------------------------------
ASSESSMENT_CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", PATIENT_TEMPLATE + "\n\nTASK: Give preliminary, educational guidance.\n" + JSON_RULES),
])

NARRATIVE_INSTRUCTIONS = """Overall urgency decided for this case: {final_urgency}.
TASK: Write a calm, easy-to-read guidance note in {language} (about 200-260 words, markdown) with these bold titles:
**What your symptoms may mean (education only)**, **What you can do now**, **When to get help urgently**,
**Please remember**. If urgency is EMERGENCY, begin with a clear instruction to seek emergency help immediately.
Never give a diagnosis or medicine doses. End by saying this is not a replacement for a doctor."""
NARRATIVE_CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", PATIENT_TEMPLATE + "\n\n" + NARRATIVE_INSTRUCTIONS),
])

CHAT_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT + "\n\nContext about this user's case:\n" + PATIENT_TEMPLATE
     + "\nOverall urgency decided: {final_urgency}.\nAnswer follow-up questions briefly (under 130 words)."),
    MessagesPlaceholder("history"),
    ("human", "{question}"),
])


def build_inputs(patient: dict, rule: dict, language: str = "English", final_urgency: str = "") -> dict:
    """Turn the validated patient dict + Python safety pre-check into prompt variables."""
    return {
        "age": patient["age"], "gender": patient["gender"], "symptoms": ", ".join(patient["symptoms"]),
        "duration": patient["duration"], "severity": patient["severity"], "conditions": patient["conditions"],
        "medications": patient["medications"], "notes": patient["notes"],
        "rule_urgency": rule["level"], "rule_reasons": "; ".join(rule["reasons"]) or "no red flags found",
        "language": language, "final_urgency": final_urgency or rule["level"],
    }
