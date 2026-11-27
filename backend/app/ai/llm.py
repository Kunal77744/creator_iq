import json
import logging
import os
import urllib.error
import urllib.request
from typing import Optional

log = logging.getLogger("creatoriq.llm")


def _api_key() -> str:
    return (os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()


def llm_is_configured() -> bool:
    return bool(_api_key())


def generate_ai_text(prompt: str, system_prompt: str = "") -> Optional[str]:
    """Call Google Gemini generateContent REST API when LLM_API_KEY is configured."""
    key = _api_key()
    if not key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 600},
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts).strip()
            return text or None
    except Exception as exc:
        log.warning("Gemini generate_ai_text fallback triggered: %s", exc)
    return None


def embed_with_llm(text: str, dimensions: int = 384) -> Optional[list[float]]:
    """Call Google Gemini text-embedding-004 with 384-dim output when LLM_API_KEY is set."""
    key = _api_key()
    if not key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={key}"
    payload = {
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": dimensions,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        values = data.get("embedding", {}).get("values")
        if isinstance(values, list) and len(values) == dimensions:
            return [float(v) for v in values]
    except Exception as exc:
        log.warning("Gemini embed_with_llm fallback triggered: %s", exc)
    return None


def call_gemini_with_tools(
    contents: list[dict],
    function_declarations: list[dict],
    system_prompt: str = "",
) -> Optional[list[dict]]:
    """Call Gemini generateContent with native functionDeclarations for agentic tool calling."""
    key = _api_key()
    if not key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"
    payload: dict = {
        "contents": contents,
        "tools": [{"functionDeclarations": function_declarations}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600},
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates") or []
        if candidates:
            return candidates[0].get("content", {}).get("parts") or None
    except Exception as exc:
        log.warning("Gemini function-calling fallback triggered: %s", exc)
    return None
