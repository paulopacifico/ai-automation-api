from __future__ import annotations

import logging
import os
import random
import time
from typing import Any, Callable

from huggingface_hub import InferenceClient, InferenceTimeoutError

logger = logging.getLogger(__name__)

DEFAULT_CLASSIFICATION: dict[str, Any] = {
    "category": "general",
    "priority": "medium",
    "estimated_duration": 30,
}

CATEGORY_LABELS = [
    "general",
    "development",
    "testing",
    "deployment",
    "maintenance",
    "documentation",
    "research",
    "design",
    "meeting",
]

PRIORITY_LABELS = ["low", "medium", "high", "urgent"]

RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}
RETRYABLE_ERROR_HINTS = (
    "rate limit",
    "too many requests",
    "timeout",
    "timed out",
    "temporarily unavailable",
    "currently loading",
    "is loading",
    "overloaded",
    "503",
    "429",
)


class AIClassifier:
    def __init__(self) -> None:
        token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not token:
            raise RuntimeError("HUGGINGFACEHUB_API_TOKEN must be set")

        self._provider = "huggingface"
        self._model = os.getenv("HF_MODEL_ID", "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        self._timeout = float(os.getenv("HF_TIMEOUT_SECONDS", "20"))
        self._max_retries = max(1, int(os.getenv("HF_MAX_RETRIES", "3")))
        self._client = InferenceClient(token=token, timeout=self._timeout)

    def classify_task(self, title: str, description: str | None) -> dict[str, Any]:
        text = self._build_task_text(title, description)

        try:
            category = self._classify_label(
                text=text,
                labels=CATEGORY_LABELS,
                hypothesis_template="This task is mainly about {}.",
                fallback=DEFAULT_CLASSIFICATION["category"],
            )
            priority = self._classify_label(
                text=text,
                labels=PRIORITY_LABELS,
                hypothesis_template="The priority level of this task is {}.",
                fallback=DEFAULT_CLASSIFICATION["priority"],
            )
            estimated_duration = self._estimate_duration(category=category, priority=priority)

            return {
                "category": category,
                "priority": priority,
                "estimated_duration": estimated_duration,
            }
        except Exception:
            logger.exception("Hugging Face classification failed; using default classification")
            return dict(DEFAULT_CLASSIFICATION)

    def _classify_label(
        self,
        *,
        text: str,
        labels: list[str],
        hypothesis_template: str,
        fallback: str,
    ) -> str:
        response = self._with_retries(
            lambda: self._client.zero_shot_classification(
                text,
                candidate_labels=labels,
                hypothesis_template=hypothesis_template,
                multi_label=False,
                model=self._model,
            ),
            operation=f"zero-shot ({','.join(labels)})",
        )
        label = self._extract_best_label(response)
        if not label:
            return fallback

        normalized = label.strip().lower()
        return normalized if normalized in labels else fallback

    def _with_retries(self, fn: Callable[[], Any], *, operation: str) -> Any:
        last_exc: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                return fn()
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                if attempt >= self._max_retries or not self._is_retryable(exc):
                    raise

                wait_seconds = random.uniform(3.0, 5.0)
                logger.warning(
                    "Hugging Face %s failed (attempt %s/%s): %s. Retrying in %.1fs",
                    operation,
                    attempt,
                    self._max_retries,
                    exc,
                    wait_seconds,
                )
                time.sleep(wait_seconds)

        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Hugging Face inference failed without a captured exception")

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        if isinstance(exc, InferenceTimeoutError):
            return True

        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        if status_code in RETRYABLE_STATUS_CODES:
            return True

        message = str(exc).lower()
        return any(hint in message for hint in RETRYABLE_ERROR_HINTS)

    @staticmethod
    def _extract_best_label(response: Any) -> str | None:
        if response is None:
            return None

        labels = getattr(response, "labels", None)
        if isinstance(labels, list) and labels:
            return str(labels[0])

        if isinstance(response, dict):
            if isinstance(response.get("labels"), list) and response["labels"]:
                return str(response["labels"][0])
            if "label" in response:
                return str(response["label"])

        if isinstance(response, list) and response:
            first = response[0]
            if isinstance(first, dict) and "label" in first:
                return str(first["label"])
            if hasattr(first, "label"):
                return str(getattr(first, "label"))

        return None

    @staticmethod
    def _estimate_duration(*, category: str, priority: str) -> int:
        category = category.lower()
        priority = priority.lower()

        special_cases: dict[tuple[str, str], int] = {
            ("urgent", "development"): 120,
            ("urgent", "deployment"): 120,
            ("high", "meeting"): 45,
            ("low", "meeting"): 15,
        }
        special_value = special_cases.get((priority, category))
        if special_value is not None:
            return special_value

        base_by_priority = {
            "low": 30,
            "medium": 45,
            "high": 90,
            "urgent": 120,
        }
        weight_by_category = {
            "general": 0,
            "development": 30,
            "testing": 15,
            "deployment": 20,
            "maintenance": 10,
            "documentation": 0,
            "research": 30,
            "design": 20,
            "meeting": -15,
        }

        base = base_by_priority.get(priority, DEFAULT_CLASSIFICATION["estimated_duration"])
        delta = weight_by_category.get(category, 0)
        duration = max(15, min(8 * 60, base + delta))
        return int(round(duration / 5) * 5)

    @staticmethod
    def _build_task_text(title: str, description: str | None) -> str:
        return f"Title: {title.strip()}\nDescription: {(description or '').strip()}"
