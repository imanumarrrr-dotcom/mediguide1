"""ChatOpenAI, the reusable LLMChain, the System/Human/AI message demo, streaming and voice transcription."""
import json
import warnings

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from prompts import ASSESSMENT_CHAT_TEMPLATE, CHAT_TEMPLATE, JSON_SCHEMA, NARRATIVE_CHAT_TEMPLATE, SYSTEM_PROMPT

warnings.filterwarnings("ignore", category=DeprecationWarning)
try:  # LLMChain lives in `langchain` 0.3; in 1.x it moved to `langchain_classic`
    from langchain.chains import LLMChain
except Exception:  # pragma: no cover
    try:
        from langchain_classic.chains import LLMChain
    except Exception:
        class LLMChain:  # minimal drop-in so the project still runs
            def __init__(self, llm, prompt, **_):
                self.chain = prompt | llm

            def invoke(self, inputs):
                return {"text": self.chain.invoke(inputs).content}


def build_llm(api_key: str, model: str, temperature: float = 0.2, json_mode: bool = False) -> ChatOpenAI:
    """Connect to OpenAI. json_mode forces a JSON object reply for the structured assessment."""
    kwargs = dict(model=model, api_key=api_key, temperature=temperature, timeout=60, max_retries=2)
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    return ChatOpenAI(**kwargs)


def validate_key(api_key: str, model: str = "gpt-4o-mini"):
    """Cheap 1-token call to check the key really works. Returns (ok, message)."""
    try:
        ChatOpenAI(model=model, api_key=api_key, max_tokens=1, timeout=20, max_retries=0).invoke("hi")
        return True, "Key verified."
    except Exception as exc:
        name = type(exc).__name__
        if "Authentication" in name:
            return False, "OpenAI rejected this key. Please check it and try again."
        if "RateLimit" in name or "insufficient_quota" in str(exc):
            return False, "Key accepted but the account has no quota/credit left."
        return False, f"Could not verify the key ({name}). Check your internet connection."


def build_assessment_chain(llm: ChatOpenAI) -> LLMChain:
    """The reusable LLMChain: ChatPromptTemplate (system + human) -> ChatOpenAI."""
    return LLMChain(llm=llm, prompt=ASSESSMENT_CHAT_TEMPLATE)


def run_assessment(chain: LLMChain, inputs: dict) -> str:
    result = chain.invoke(inputs)
    return result["text"] if isinstance(result, dict) else str(result)


def stream_narrative(llm: ChatOpenAI, inputs: dict):
    """Generator for st.write_stream(): yields the guidance note chunk by chunk."""
    messages = NARRATIVE_CHAT_TEMPLATE.format_messages(**inputs)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content


def stream_chat(llm: ChatOpenAI, inputs: dict, history: list, question: str):
    """Follow-up Q&A with conversation memory (HumanMessage / AIMessage history)."""
    messages = CHAT_TEMPLATE.format_messages(history=history, question=question, **inputs)
    for chunk in llm.stream(messages):
        if chunk.content:
            yield chunk.content


def message_demo(language: str = "English") -> list:
    """Shows how System / Human / AI messages are represented in a conversation."""
    sample = {**JSON_SCHEMA, "summary": "Mild cold-like symptoms...", "urgency_level": "LOW"}
    return [SystemMessage(content=SYSTEM_PROMPT.format(language=language)),
            HumanMessage(content="Age 25, runny nose and sore throat for 2 days, severity 2."),
            AIMessage(content=json.dumps(sample))]


def transcribe_audio(api_key: str, audio_bytes: bytes) -> str:
    """Voice symptom input: OpenAI speech-to-text. Returns the transcript text."""
    from openai import OpenAI
    result = OpenAI(api_key=api_key, timeout=60).audio.transcriptions.create(
        model="whisper-1", file=("voice.wav", audio_bytes))
    return result.text.strip()
