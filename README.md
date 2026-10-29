# 🩺 MediGuide AI — AI-Powered Medical Symptom Assessment & Patient Guidance Assistant

A **LangChain + OpenAI + Streamlit** prototype that turns symptoms into structured, safety-first, educational guidance.

> ⚠️ **Educational prototype only.** NOT a doctor, never a confirmed diagnosis, not a replacement for professional
> care or emergency services. In an emergency call your local emergency number immediately.
> The disclaimer is shown in the sidebar, on every page and in the results.

## Features
- 🔐 **API-key gate**: the console unlocks only after a verified OpenAI key (session memory only, never saved)
- 🎨 Animated UI: dark/light, 5 accent palettes, colour-wipe theme transition, animated urgency meter, RTL for Urdu/Arabic
- 📝 Form: age (`text_input`), gender, symptoms (`multiselect` + free text), duration, severity slider, conditions, medications, notes, answer language
- 🛡️ **Python safety net**: rule-based red-flag screen sets a *minimum* urgency; the AI can only raise it. Self-harm keyword check shows a supportive message.
- 🤖 `ChatOpenAI`, `PromptTemplate`, `ChatPromptTemplate`, System/Human/AI messages, reusable `LLMChain`
- 🧾 Exact JSON schema, fences stripped, `try/except` parsing, rule-based fallback (never crashes)
- ⌨️ Streaming guidance note via `llm.stream()` + `st.write_stream()`
- ⚡ `InMemoryCache` / `SQLiteCache` / Off, switchable in the sidebar
- Extras: test scenarios loader, voice symptom input (Whisper), follow-up chat with memory, urgency analytics, report download, 9 answer languages

## Setup
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
Paste your `sk-...` key on the unlock screen. Optional: copy `.env.example` to `.env` and set
`MEDIGUIDE_ALLOW_ENV_KEY=1` for a "Use key from .env" button. `.env` is git-ignored — never commit a real key.

## Caching: InMemoryCache vs SQLiteCache
`set_llm_cache(...)` registers one global cache that LangChain checks before every model call.
| | InMemoryCache | SQLiteCache |
|---|---|---|
| Stored in | RAM | `data/mediguide_cache.db` |
| Speed | Fastest | Fast, slightly slower |
| Survives restart | No | Yes |
| Best for | One session | Reuse across sessions |
Submit the same form twice: the second run is instant and shows "cache hit".

## Test scenarios (also in the app's loader)
1. Age 25, runny nose + sore throat → LOW  2. Age 40, fever + cough, 4-7 days → MEDIUM/HIGH
3. Chest pain + shortness of breath → EMERGENCY  4. Same form twice → faster  5. Empty symptoms → warning, no API call
6. Language = Urdu → Urdu guidance. Run `pytest tests` for the offline safety tests.

## Structure
```
app.py  requirements.txt  .env.example  README.md
src/ config.py prompts.py chains.py cache_manager.py utils.py theme.py
tests/test_safety.py   docs/Medical_AI_Assignment.pdf
```
