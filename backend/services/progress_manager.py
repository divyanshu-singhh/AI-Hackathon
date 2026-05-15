"""Thread-safe WebSocket progress events for image processing jobs."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from threading import RLock
from typing import Any


@dataclass
class Subscriber:
    loop: asyncio.AbstractEventLoop
    queue: asyncio.Queue


class ProgressManager:
    """Keep short in-memory job history and fan out events to WebSocket clients."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = {}
        self._history: dict[str, list[dict[str, Any]]] = {}
        self._lock = RLock()

    async def subscribe(self, job_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        subscriber = Subscriber(asyncio.get_running_loop(), queue)
        with self._lock:
            self._subscribers.setdefault(job_id, []).append(subscriber)
            for event in self._history.get(job_id, []):
                queue.put_nowait(event)
        return queue

    async def unsubscribe(self, job_id: str, queue: asyncio.Queue) -> None:
        with self._lock:
            subscribers = self._subscribers.get(job_id, [])
            self._subscribers[job_id] = [item for item in subscribers if item.queue is not queue]
            if not self._subscribers[job_id]:
                self._subscribers.pop(job_id, None)

    def emit(self, job_id: str | None, event: dict[str, Any]) -> None:
        if not job_id:
            return

        payload = {
            "job_id": job_id,
            "timestamp": time.time(),
            "stage_id": event.get("stage_id", ""),
            "stage": event.get("stage", ""),
            "status": event.get("status", "running"),
            "percent": int(event.get("percent", 0) or 0),
            "message": event.get("message", ""),
            "model_name": event.get("model_name", ""),
            "model_type": event.get("model_type", "Local"),
            "tokens_used": int(event.get("tokens_used", 0) or 0),
            "prompt_tokens": int(event.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(event.get("completion_tokens", 0) or 0),
            "estimated_cost": str(event.get("estimated_cost", "") or ""),
        }

        with self._lock:
            history = self._history.setdefault(job_id, [])
            history.append(payload)
            if len(history) > 100:
                del history[: len(history) - 100]
            subscribers = list(self._subscribers.get(job_id, []))

        for subscriber in subscribers:
            subscriber.loop.call_soon_threadsafe(subscriber.queue.put_nowait, payload)

    def clear(self, job_id: str) -> None:
        with self._lock:
            self._history.pop(job_id, None)


progress_manager = ProgressManager()


def model_type_for(model_name: str, local_default: str = "Local") -> str:
    """Classify visible model/tool type for the UI."""
    if not model_name:
        return local_default

    open_source_prefixes = (
        "qwen/",
        "meta-llama/",
        "openrouter/meta-llama/",
        "deepseek/",
        "google/gemma",
        "openai/gpt-oss",
    )
    proprietary_prefixes = (
        "openai/",
        "anthropic/",
        "google/gemini",
        "x-ai/",
        "minimax/",
        "moonshotai/",
        "z-ai/",
        "gemini/",
        "vertex-googleaistudio/",
    )
    if model_name.startswith(open_source_prefixes):
        return "Open source model"
    if model_name.startswith(proprietary_prefixes):
        return "Paid/proprietary model"
    return local_default
