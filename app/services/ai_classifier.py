from __future__ import annotations

import json
import logging
import os
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_CLASSIFICATION: dict[str, Any] = {
    "category": "general",
    "priority": "medium",
    "estimated_duration": 30,
}


class AIClassifier:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = OpenAI(api_key=api_key, timeout=10.0)

    def classify_task(self, title: str, description: str | None) -> dict[str, Any]:
        prompt = (
            "Classify the task and respond ONLY with JSON containing keys: "
            "category (string), priority (low|medium|high), estimated_duration (integer minutes).\n\n"
            f"Title: {title}\n"
            f"Description: {description or ''}"
        )

        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        try:
            content = response.choices[0].message.content or ""
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON returned by AI") from exc

        category = str(payload.get("category", DEFAULT_CLASSIFICATION["category"]))
        priority = str(payload.get("priority", DEFAULT_CLASSIFICATION["priority"])).lower()
        if priority not in {"low", "medium", "high"}:
            priority = DEFAULT_CLASSIFICATION["priority"]
        try:
            estimated_duration = int(payload.get("estimated_duration", DEFAULT_CLASSIFICATION["estimated_duration"]))
        except (TypeError, ValueError):
            estimated_duration = DEFAULT_CLASSIFICATION["estimated_duration"]

        return {
            "category": category,
            "priority": priority,
            "estimated_duration": estimated_duration,
        }
