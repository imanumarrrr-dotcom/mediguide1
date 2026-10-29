"""MediGuide AI — Streamlit UI.  Run with:  streamlit run app.py
Educational prototype: NOT a doctor, never a confirmed diagnosis."""
import copy
import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from src.cache_manager import cache_info, clear_cache, configure_cache
from src.chains import (build_assessment_chain, build_llm, message_demo, run_assessment, stream_chat,
                        stream_narrative, transcribe_audio, validate_key)
from src.config import (ACCENTS, APP_ICON, APP_NAME, CACHE_OPTIONS, DEFAULT_MODEL, DISCLAIMER, DURATIONS,
                        EMERGENCY_NUMBERS, GENDERS, LANGUAGES, MODEL_OPTIONS, RTL_LANGUAGES, SCENARIOS,
                        SYMPTOMS, TAGLINE, URGENCY_COLORS, env_api_key)
from src.prompts import PATIENT_PROMPT, build_inputs
from src.theme import inject_css, plotly_layout
from src.utils import (LEVELS, crisis_check, fallback_assessment, parse_age, parse_assessment, report_markdown,
                       rule_urgency)

st.set_page_config(page_title=f"{APP_NAME} — Symptom Guidance", page_icon=APP_ICON, layout="wide")

NAV = ["🩺 Assessment", "📊 Results", "💬 Ask MediGuide", "🛠️ Console"]
INPUT_KEYS = ["age", "gender", "symptoms", "free", "duration", "severity", "conds", "meds", "notes", "language"]
SETTING_KEYS = ["model", "temperature", "cache_mode", "mode", "accent", "nav", "country"]
DEFAULTS = dict(api_key="", key_ok=False, model=DEFAULT_MODEL, temperature=0.2, cache_mode="In-memory",
                mode="Dark", accent="Teal Care", nav=NAV[0], country="Pakistan", run_requested=False,
                pending_stream=False, form_error=None, patient=None, rule=None, assessment=None, inputs=None,
                narrative="", warning=None, crisis=False, history=[], chat=[], last_ms=None, cache_hit=False,
                raw_json="", age="", gender=GENDERS[0], symptoms=[], free="", duration=DURATIONS[1],
                severity=3, conds="", meds="", notes="", language="English")
S = st.session_state
for _k, _v in DEFAULTS.items():
    S.setdefault(_k, copy.deepcopy(_v))
for _k in INPUT_KEYS + SETTING_KEYS:  # keep widget values alive while their page is not shown
    S[_k] = S[_k]
S["sb_language"] = S["language"]  # sidebar language selector mirrors the form's answer language

st.markdown(inject_css(S.mode, S.accent), unsafe_allow_html=True)
if S.language in RTL_LANGUAGES:  # Urdu / Arabic read right-to-left
    st.markdown("<style>.st-key-results [data-testid='stMarkdownContainer']"
                "{direction:rtl;text-align:right}</style>", unsafe_allow_html=True)


# ----------------------------------------------------------------- helpers
def emergency_number() -> str:
    return EMERGENCY_NUMBERS.get(S.country, "your local emergency number")


def badge(level: str) -> str:
    return f'<span class="badge {level}">{level}</span>'


def safety_banner() -> None:
    """Shown on EVERY page: disclaimer + emergency instruction."""
    st.markdown(f'<div class="safety">🚨 <b>Emergency?</b> Call {emergency_number()} immediately. '
                f'{DISCLAIMER}</div>', unsafe_allow_html=True)


def hero(title: str, sub: str) -> None:
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{sub}</p></div>', unsafe_allow_html=True)


def collect_symptoms() -> list:
    return list(S.symptoms) + [x.strip() for x in S.free.split(",") if x.strip()]


def make_patient(age: int) -> dict:
    return dict(age=age, gender=S.gender, symptoms=collect_symptoms(), duration=S.duration,
                severity=int(S.severity), conditions=S.conds.strip() or "None reported",
                medications=S.meds.strip() or "None reported", notes=S.notes.strip() or "None")


# --------------------------------------------------------------- callbacks
def load_scenario() -> None:
    sc = SCENARIOS[S.scn]
    S.age, S.gender, S.symptoms, S.free, S.duration = sc["age"], sc["gender"], list(sc["symptoms"]), "", sc["duration"]
    S.severity, S.conds, S.meds, S.notes, S.language = sc["severity"], sc["conds"], sc["meds"], sc["notes"], sc["language"]


def request_run() -> None:
    """Validate BEFORE any API call: empty symptoms or a bad age only show a warning."""
    S.form_error = None
    ok, _, msg = parse_age(S.age)
    if not ok:
        S.form_error = msg
    elif not collect_symptoms():
        S.form_error = "Please select at least one symptom (or describe it) — no request was sent to the AI."
    else:
        S.run_requested, S.nav = True, NAV[1]


def reset_session() -> None:
    keep = {"api_key", "key_ok", "mode", "accent", "model", "country"}
    for k in list(S.keys()):
        if k not in keep:
            del S[k]


def lock_console() -> None:
    S.api_key, S.key_ok = "", False


# ------------------------------------------------------------------ sidebar
def sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## {APP_ICON} {APP_NAME}")
        st.caption(TAGLINE)
        st.markdown("##### 🎨 Appearance")
        st.radio("Mode", ["Dark", "Light"], key="mode", horizontal=True)
        st.selectbox("Accent palette", list(ACCENTS), key="accent")
        st.selectbox("🌍 Country (emergency number)", list(EMERGENCY_NUMBERS), key="country")
        if S.key_ok:
            with st.expander("🤖 Model configuration", expanded=True):
                st.selectbox("OpenAI model", MODEL_OPTIONS, key="model")
                st.slider("Creativity (temperature)", 0.0, 1.0, step=0.1, key="temperature")
                st.selectbox("🌐 Answer language", LANGUAGES, key="sb_language",
                             on_change=lambda: S.__setitem__("language", S.sb_language))
            with st.expander("⚡ Caching"):
                st.radio("Cache type", CACHE_OPTIONS, key="cache_mode")
                st.caption("In-memory = fastest, lost on restart. SQLite = file on disk, survives restarts. "
                           "A cache hit makes no new API call.")
                st.button("🧹 Clear this cache", on_click=lambda: clear_cache(S.cache_mode))
            c1, c2 = st.columns(2)
            c1.button("🔄 Reset", on_click=reset_session, help="Clear all data and results")
            c2.button("🔒 Lock", on_click=lock_console, help="Forget the API key")
        with st.expander("ℹ️ About"):
            st.markdown("**AI-Powered Medical Symptom Assessment & Patient Guidance Assistant**  \n"
                        "LangChain + OpenAI + Streamlit. Python runs a safety pre-check; the AI explains.")
        st.markdown(f'<div class="disclaimer">⚠️ {DISCLAIMER}</div>', unsafe_allow_html=True)


# -------------------------------------------------------------- API key gate
def gate() -> None:
    hero(f"{APP_ICON} Welcome to {APP_NAME}", "Enter your OpenAI API key to unlock the console.")
    safety_banner()
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid, st.container(border=True):
        st.markdown("### 🔐 Unlock the console")
        st.caption("Your key stays in this browser session's memory only — never written to disk or logged.")
        key = st.text_input("OpenAI API key", type="password", placeholder="sk-...", label_visibility="collapsed")
        use_env = bool(env_api_key()) and st.button("Use key from .env", width="stretch")
        if st.button("🔓 Unlock console", width="stretch") or use_env:
            key = env_api_key() if use_env else key.strip()
            if not key.startswith("sk-"):
                st.error("An OpenAI key starts with `sk-`. Please paste a valid key.")
            else:
                with st.spinner("Verifying key with OpenAI..."):
                    ok, msg = validate_key(key, S.model)
                if ok:
                    S.api_key, S.key_ok = key, True
                    st.toast("Console unlocked 🎉")
                    st.rerun()
                st.error(msg)
        st.markdown("[Get a key at platform.openai.com](https://platform.openai.com/api-keys)")


# ---------------------------------------------------------- page: assessment
def page_assessment() -> None:
    hero("How are you feeling?", "Share your symptoms and get calm, structured, educational guidance.")
    safety_banner()
    with st.expander("⚡ Try a test scenario"):
        a, b = st.columns([4, 1])
        a.selectbox("Scenario", list(SCENARIOS), key="scn", label_visibility="collapsed")
        b.button("Load", on_click=load_scenario, width="stretch")
    with st.expander("🎙️ Voice symptom input (optional)"):
        audio = st.audio_input("Record your symptoms")
        if audio is not None and st.button("Transcribe into the symptoms box"):
            try:
                with st.spinner("Transcribing..."):
                    text = transcribe_audio(S.api_key, audio.getvalue())
                S.free = f"{S.free}, {text}".strip(", ")
                st.success(f"Added: {text}")
            except Exception as exc:
                st.error(f"Could not transcribe ({type(exc).__name__}).")
    if S.form_error:
        st.warning(S.form_error)
    with st.form("patient_form"):
        c1, c2, c3 = st.columns(3)
        c1.text_input("Patient age", placeholder="e.g. 25", key="age")
        c2.selectbox("Gender", GENDERS, key="gender")
        c3.selectbox("Answer language", LANGUAGES, key="language")
        st.multiselect("Symptoms", SYMPTOMS, key="symptoms", placeholder="Choose one or more symptoms")
        st.text_input("Other symptoms (optional, comma separated)", key="free")
        d1, d2 = st.columns(2)
        d1.selectbox("How long?", DURATIONS, key="duration")
        d2.slider("Severity (1 = mild, 10 = worst)", 1, 10, key="severity")
        st.text_area("Existing medical conditions", key="conds", height=70)
        st.text_area("Current medications", key="meds", height=70)
        st.text_area("Additional notes", key="notes", height=70)
        st.form_submit_button("🔍 Get guidance", on_click=request_run)


# ------------------------------------------------------------- page: results
def run_pipeline() -> None:
    S.run_requested = False
    patient = make_patient(parse_age(S.age)[1])
    rule = rule_urgency(patient)
    S.crisis = crisis_check(S.free, S.notes, S.conds)
    inputs = build_inputs(patient, rule, S.language)
    configure_cache(S.cache_mode)
    t0 = time.perf_counter()
    try:
        with st.spinner("🧠 Running the safety pre-check and AI assessment..."):
            chain = build_assessment_chain(build_llm(S.api_key, S.model, S.temperature, json_mode=True))
            raw = run_assessment(chain, inputs)
        a, warning = parse_assessment(raw, patient, rule)
    except Exception as exc:
        raw, a = "", fallback_assessment(patient, rule)
        warning = f"AI call failed ({type(exc).__name__}). Showing rule-based guidance instead."
    ms = (time.perf_counter() - t0) * 1000
    inputs["final_urgency"] = a["urgency_level"]
    S.update(patient=patient, rule=rule, assessment=a, inputs=inputs, warning=warning, raw_json=raw, last_ms=ms,
             cache_hit=(S.cache_mode != "Off" and ms < 400 and not warning), narrative="",
             pending_stream=not (warning or "").startswith("AI call failed"))
    S.history.append(dict(Time=time.strftime("%H:%M:%S"), Age=patient["age"], Symptoms=len(patient["symptoms"]),
                          Severity=patient["severity"], Urgency=a["urgency_level"]))


def urgency_alert(level: str) -> None:
    msgs = {"EMERGENCY": f"🚨 EMERGENCY — seek emergency help IMMEDIATELY. Call {emergency_number()} or go to the "
                         "nearest emergency room now. Do not wait.",
            "HIGH": "⚠️ HIGH — please contact a doctor or urgent-care service today.",
            "MEDIUM": "ℹ️ MEDIUM — arrange to see a healthcare professional in the next few days.",
            "LOW": "✅ LOW — monitor your symptoms and rest. See a doctor if they worsen or last."}
    {"EMERGENCY": st.error, "HIGH": st.warning, "MEDIUM": st.info, "LOW": st.success}[level](msgs[level])


def page_results() -> None:
    if S.run_requested:
        run_pipeline()
    a, p = S.assessment, S.patient
    if not a:
        hero("Your results", "No assessment yet.")
        safety_banner()
        st.info("Go to **🩺 Assessment**, fill in the form and press **Get guidance**.")
        return
    level, idx = a["urgency_level"], LEVELS.index(a["urgency_level"])
    with st.container(key="results"):
        hero("Your guidance dashboard", "Educational, preliminary information — never a diagnosis.")
        safety_banner()
        if S.warning:
            st.warning(S.warning)
        if S.crisis:
            st.error("💙 You mentioned thoughts of harming yourself. You are not alone — please contact emergency "
                     f"services ({emergency_number()}) or a crisis line in your country right now, or tell someone you trust.")
        if S.last_ms is not None:
            st.caption(f"⏱️ Analysis took {S.last_ms:.0f} ms" + (" — ⚡ cache hit, no API call made" if S.cache_hit else "")
                       + f" · cache: {S.cache_mode}")
        color = URGENCY_COLORS[level]
        meter = "".join(f'<div class="{"on" if i <= idx else ""}" style="color:{color};'
                        f'{"background:" + color if i <= idx else ""}"></div>' for i in range(4))
        st.markdown(f'<div class="urgency-card"><b>Urgency level</b> &nbsp; {badge(level)} &nbsp; '
                    f'<span style="opacity:.75">🤖 AI: {a["ai_urgency"]} · 🐍 Python safety floor: {S.rule["level"]}</span>'
                    f'<div class="meter">{meter}</div></div>', unsafe_allow_html=True)
        urgency_alert(level)
        if S.rule["level"] != "LOW" and S.rule["reasons"]:
            st.caption("Python safety pre-check: " + "; ".join(S.rule["reasons"]))
        m = st.columns(4)
        m[0].metric("Age", p["age"])
        m[1].metric("Symptoms", len(p["symptoms"]))
        m[2].metric("Severity", f"{p['severity']}/10")
        m[3].metric("Duration", p["duration"])

        t1, t2, t3, t4, t5 = st.tabs(["📋 Summary", "🔍 Possible conditions", "✅ Next steps & questions",
                                      "🚨 Warning signs", "📈 Severity"])
        with t1:
            st.markdown("##### Patient symptom summary")
            st.info(a["summary"])
            st.caption("Symptoms: " + ", ".join(p["symptoms"]))
        with t2:
            st.warning("For education only — these are NOT diagnoses.")
            for c in a["possible_conditions"] or [{"name": "None listed", "reason": "No AI suggestions available."}]:
                with st.expander(f"🔎 {c['name']}"):
                    st.write(c["reason"])
        with t3:
            x, y = st.columns(2)
            x.markdown("##### Recommended next steps")
            for s in a["recommended_next_steps"]:
                x.success(s)
            y.markdown("##### Questions to ask your doctor")
            for q in a["questions_for_doctor"]:
                y.markdown(f"❓ {q}")
        with t4:
            st.error("Seek emergency help immediately if you notice any of these:")
            for w in a["warning_signs"]:
                st.markdown(f"- 🚩 {w}")
        with t5:
            fig = go.Figure(go.Indicator(mode="gauge+number", value=p["severity"], title={"text": "Reported severity"},
                                         gauge={"axis": {"range": [0, 10]}, "bar": {"color": color}}))
            fig.update_layout(height=280, **plotly_layout(S.mode))
            st.plotly_chart(fig, width="stretch")

        st.markdown("#### ✍️ Guidance note")
        if S.pending_stream:
            S.pending_stream = False
            try:
                S.narrative = st.write_stream(stream_narrative(build_llm(S.api_key, S.model, S.temperature), S.inputs))
            except Exception as exc:
                st.error(f"Streaming failed ({type(exc).__name__}). Please try again.")
        else:
            st.markdown(S.narrative or "_No guidance note yet._")
        d1, d2 = st.columns(2)
        d1.download_button("⬇️ Download report (.md)", report_markdown(p, a, S.narrative), "mediguide_report.md", width="stretch")
        d2.download_button("⬇️ Download AI JSON", S.raw_json or "{}", "mediguide_assessment.json", width="stretch")


# ----------------------------------------------------------------- page: chat
def page_chat() -> None:
    hero("Ask MediGuide", "Follow-up questions about your guidance — with conversation memory.")
    safety_banner()
    if not S.inputs:
        st.info("Run an assessment first so MediGuide has context for your questions.")
        return
    for msg in S.chat:
        with st.chat_message("user" if isinstance(msg, HumanMessage) else "assistant"):
            st.markdown(msg.content)
    q = st.chat_input("e.g. What can I do at home for a sore throat?")
    if q:
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            try:
                configure_cache(S.cache_mode)
                reply = st.write_stream(stream_chat(build_llm(S.api_key, S.model, S.temperature), S.inputs, list(S.chat), q))
                S.chat += [HumanMessage(content=q), AIMessage(content=reply)]
            except Exception as exc:
                st.error(f"Chat failed ({type(exc).__name__}).")
    if S.chat:
        st.button("🗑️ Clear conversation", on_click=lambda: S.chat.clear())


# --------------------------------------------------------------- page: console
def page_console() -> None:
    hero("Developer console", "See how LangChain, prompts, messages, caching and the safety net work.")
    safety_banner()
    inputs = S.inputs
    if not inputs:  # sample data so the console is useful before the first run
        sc = SCENARIOS[list(SCENARIOS)[1]]
        pat = dict(age=int(sc["age"]), gender=sc["gender"], symptoms=sc["symptoms"], duration=sc["duration"],
                   severity=sc["severity"], conditions="None reported", medications=sc["meds"], notes=sc["notes"])
        inputs = build_inputs(pat, rule_urgency(pat), S.language)
    t1, t2, t3, t4, t5 = st.tabs(["🐍 Python vs 🤖 AI", "💬 Messages & prompts", "⚡ Cache", "📈 Analytics", "🧪 Raw output"])
    with t1:
        st.table(pd.DataFrame({
            "Python (deterministic)": ["Age validation, empty-symptom guard", "Red-flag rules set a MINIMUM urgency",
                                       "Self-harm keyword check", "Parses JSON safely, fallback on failure"],
            "LLM (probabilistic)": ["Explains symptoms in plain language", "Suggests educational possible conditions",
                                    "Writes next steps and doctor questions", "Can only RAISE urgency, never lower it"]}))
    with t2:
        for msg in message_demo(S.language):
            with st.expander(type(msg).__name__):
                st.code(msg.content, language="text")
        st.markdown("**PromptTemplate rendered with the patient data**")
        st.code(PATIENT_PROMPT.format(**{k: inputs[k] for k in PATIENT_PROMPT.input_variables}), language="text")
    with t3:
        info = cache_info(S.cache_mode)
        c = st.columns(3)
        c[0].metric("Cache type", info["mode"])
        c[1].metric("Entries", info["entries"])
        c[2].metric("Survives restart", "Yes" if info["survives_restart"] else "No")
        st.caption(f"Location: {info['location']}. Submit the same form twice: the second run is instant.")
    with t4:
        if S.history:
            df = pd.DataFrame(S.history)
            counts = df["Urgency"].value_counts().reindex(LEVELS, fill_value=0).reset_index()
            counts.columns = ["Urgency", "Count"]
            fig = px.bar(counts, x="Urgency", y="Count", color="Urgency", color_discrete_map=URGENCY_COLORS,
                         title="Urgency distribution this session")
            fig.update_layout(**plotly_layout(S.mode))
            st.plotly_chart(fig, width="stretch")
            st.dataframe(df, width="stretch")
        else:
            st.info("Run an assessment to see session analytics.")
    with t5:
        st.code(S.raw_json or "Run an assessment first.", language="json")


# ---------------------------------------------------------------------- main
sidebar()
if not S.key_ok:
    gate()
else:
    st.radio("Navigate", NAV, key="nav", horizontal=True, label_visibility="collapsed")
    {NAV[0]: page_assessment, NAV[1]: page_results, NAV[2]: page_chat, NAV[3]: page_console}[S.nav]()
