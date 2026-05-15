"""OpenAI-compatible client for the internal LLM gateway."""

import base64
import json
import mimetypes
import re
from pathlib import Path
from typing import Any

import requests

from config import IM_LLM_API_KEY, IM_LLM_BASE_URL


def image_to_data_url(path: str | Path) -> str:
    """Read an image from disk and return an OpenAI-style base64 data URL."""
    image_path = Path(path)
    mime_type = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"


def safe_parse_json(text: str | dict[str, Any] | None) -> dict[str, Any]:
    """Parse JSON even when a model wraps it in markdown or adds light extra text."""
    if isinstance(text, dict):
        return text
    if not text:
        return {}

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            return {"parse_error": "No JSON object found", "raw_text": cleaned[:1000]}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            return {"parse_error": str(exc), "raw_text": cleaned[:1000]}


def chat_completion(
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
    max_tokens: int = 1200,
) -> dict[str, Any]:
    """Call the internal gateway and return parsed JSON from the assistant message."""
    if not IM_LLM_API_KEY or IM_LLM_API_KEY == "replace_with_your_access_key":
        raise RuntimeError("IM_LLM_API_KEY is not configured")

    url = f"{IM_LLM_BASE_URL}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {IM_LLM_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=90)
    if response.status_code >= 400:
        safe_body = response.text[:1200]
        raise RuntimeError(f"LLM gateway error {response.status_code}: {safe_body}")

    data = response.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    parsed = safe_parse_json(content)
    parsed["_raw_gateway_response"] = data
    return parsed
