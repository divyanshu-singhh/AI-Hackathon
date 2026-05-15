"""OpenAI-compatible client for the internal LLM gateway."""

import base64
import json
import logging
import mimetypes
import re
from pathlib import Path
from typing import Any

import requests

from config import IM_LLM_API_KEY, IM_LLM_BASE_URL, LLM_DEBUG

logger = logging.getLogger("ai_image_parser.llm")


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

    if LLM_DEBUG:
        logger.warning(
            "LLM request model=%s url=%s message_count=%s has_image=%s max_tokens=%s",
            model,
            url,
            len(messages),
            _messages_have_image(messages),
            max_tokens,
        )

    response = requests.post(url, headers=headers, json=payload, timeout=90)
    if LLM_DEBUG:
        logger.warning(
            "LLM response status=%s call_id=%s model_group=%s cost=%s",
            response.status_code,
            response.headers.get("x-litellm-call-id", ""),
            response.headers.get("x-litellm-model-group", ""),
            response.headers.get("x-litellm-response-cost", ""),
        )

    if response.status_code >= 400:
        safe_body = response.text[:1200]
        if LLM_DEBUG:
            logger.warning("LLM error body preview=%s", safe_body)
        raise RuntimeError(f"LLM gateway error {response.status_code}: {safe_body}")

    data = response.json()
    content = _extract_message_content(data)
    if LLM_DEBUG:
        logger.warning(
            "LLM response usage=%s content_preview=%s",
            data.get("usage", {}),
            str(content)[:600],
        )
    parsed = safe_parse_json(content)
    if LLM_DEBUG:
        logger.warning("LLM parsed keys=%s parse_error=%s", list(parsed.keys()), parsed.get("parse_error", ""))
    parsed["_llm_meta"] = _llm_meta(model, data, response)
    parsed["_raw_gateway_response"] = data
    return parsed


def _llm_meta(model: str, data: dict[str, Any], response: requests.Response) -> dict[str, Any]:
    usage = data.get("usage", {}) or {}
    return {
        "model_name": model,
        "response_model": data.get("model", ""),
        "model_group": response.headers.get("x-litellm-model-group", ""),
        "call_id": response.headers.get("x-litellm-call-id", ""),
        "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
        "estimated_cost": response.headers.get("x-litellm-response-cost", ""),
    }


def _extract_message_content(data: dict[str, Any]) -> str:
    """Extract assistant text from OpenAI-compatible chat completion responses."""
    message = data.get("choices", [{}])[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content or "")


def _messages_have_image(messages: list[dict[str, Any]]) -> bool:
    """Return whether a request contains image input without logging image data."""
    for message in messages:
        content = message.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") == "image_url":
                    return True
    return False
