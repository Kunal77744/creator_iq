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


def _chat_models() -> list[str]:
    primary = (os.getenv("LLM_MODEL") or "gemini-3.8-flash").strip()
    candidates = [primary, "gemini-3.8-flash", "gemini-3.6-flash", "gemini-2.5-flash"]
    seen: list[str] = []
    for m in candidates:
        if m and m not in seen:
            seen.append(m)
    return seen


def _post_generate_content(payload: dict, key: str, timeout: int) -> Optional[dict]:
    for model in _chat_models():
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 429, 500, 502, 503, 504):
                log.warning("Gemini model %s returned HTTP %s, trying fallback model", model, exc.code)
                continue
            raise
    return None


def generate_ai_text(prompt: str, system_prompt: str = "") -> Optional[str]:
    """Call Google Gemini generateContent REST API when LLM_API_KEY is configured."""
    key = _api_key()
    if not key:
        return None

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 600},
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
    try:
        data = _post_generate_content(payload, key, timeout=15)
        if not data:
            return None
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts).strip()
            return text or None
    except Exception as exc:
        log.warning("Gemini generate_ai_text fallback triggered: %s", exc)
    return None


def embed_with_llm(text: str, dimensions: int = 384) -> Optional[list[float]]:
    """Call Google Gemini gemini-embedding-001 with 384-dim output when LLM_API_KEY is set."""
    key = _api_key()
    if not key:
        return None

    embed_model = (os.getenv("LLM_EMBED_MODEL") or "gemini-embedding-001").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{embed_model}:embedContent?key={key}"
    payload = {
        "model": f"models/{embed_model}",
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

    payload: dict = {
        "contents": contents,
        "tools": [{"functionDeclarations": function_declarations}],
        "generationConfig": {"temperature": 0.2, "maxOutputTokens": 600},
    }
    if system_prompt:
        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

    try:
        data = _post_generate_content(payload, key, timeout=20)
        if not data:
            return None
        candidates = data.get("candidates") or []
        if candidates:
            return candidates[0].get("content", {}).get("parts") or None
    except Exception as exc:
        log.warning("Gemini function-calling fallback triggered: %s", exc)
    return None
