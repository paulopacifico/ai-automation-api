from __future__ import annotations

import json
import logging
import os
from typing import Any, Literal

import anthropic
from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_CLASSIFICATION: dict[str, Any] = {
    "category": "general",
    "priority": "medium",
    "estimated_duration": 30,
}


class AIClassifier:
    def __init__(self) -> None:
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if openai_key:
            self._provider: Literal["openai", "anthropic"] = "openai"
            self._openai_client = OpenAI(api_key=openai_key, timeout=10.0)
            self._anthropic_client = None
        elif anthropic_key:
            self._provider = "anthropic"
            self._openai_client = None
            self._anthropic_client = anthropic.Anthropic(api_key=anthropic_key, timeout=10.0)
        else:
            raise RuntimeError("OPENAI_API_KEY or ANTHROPIC_API_KEY must be set")

    def classify_task(self, title: str, description: str | None) -> dict[str, Any]:
        if self._provider == "openai":
            return self._classify_openai(title, description)
        return self._classify_anthropic(title, description)

    def _classify_openai(self, title: str, description: str | None) -> dict[str, Any]:
        prompt = self._build_prompt(title, description)
        response = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        try:
            content = response.choices[0].message.content or ""
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON returned by OpenAI") from exc

        return self._normalize_payload(payload)

    def _classify_anthropic(self, title: str, description: str | None) -> dict[str, Any]:
        prompt = self._build_prompt(title, description)
        message = self._anthropic_client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        content = self._extract_anthropic_text(message)

        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON returned by Anthropic") from exc

        return self._normalize_payload(payload)

    @staticmethod
    def _build_prompt(title: str, description: str | None) -> str:
        return (
            "Classify the task and respond ONLY with JSON containing keys: "
            "category (string), priority (low|medium|high), estimated_duration (integer minutes).\n\n"
            f"Title: {title}\n"
            f"Description: {description or ''}"
        )

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
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

    @staticmethod
    def _extract_anthropic_text(message: Any) -> str:
        content = getattr(message, "content", None)
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
                item_text = getattr(item, "text", None) or (item.get("text") if isinstance(item, dict) else None)
                if item_type == "text" and item_text:
                    parts.append(str(item_text))
            if parts:
                return "".join(parts).strip()

        if isinstance(content, str):
            return content.strip()

        raise ValueError("No text content returned by Anthropic")
