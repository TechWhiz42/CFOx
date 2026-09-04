import json
import logging
from typing import Literal

import ollama
from pydantic import BaseModel, Field, ValidationError

from app.config import settings

logger = logging.getLogger("cfox.ai")

MODEL = settings.AI_MODEL


class FinancialInsight(BaseModel):
    summary: str = Field(
        min_length=1,
        max_length=1000,
    )

    severity: Literal[
        "normal",
        "warning",
        "critical",
    ]

    evidence: list[str] = Field(
        default_factory=list,
        max_length=2,
    )

    impact: str = Field(
        default="",
        max_length=1000,
    )

    recommendations: list[str] = Field(
        default_factory=list,
        max_length=2,
    )


def _fallback_insight(reason: str) -> dict:
    fallback = FinancialInsight(
        summary="Financial insight is temporarily unavailable.",
        severity="normal",
        evidence=[],
        impact=reason,
        recommendations=[],
    )

    return fallback.model_dump()


def _clean_model_output(content: str) -> str:
    content = content.strip()

    if content.startswith("```"):
        lines = content.splitlines()

        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    if not content.startswith("{"):
        start = content.find("{")
        end = content.rfind("}")

        if start != -1 and end != -1 and end > start:
            content = content[start:end + 1].strip()

    return content


def _parse_and_validate(content: str) -> dict:
    content = _clean_model_output(content)

    if not content:
        raise ValueError("AI returned an empty response.")

    try:
        raw_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "AI returned invalid JSON."
        ) from exc

    if not isinstance(raw_data, dict):
        raise ValueError(
            "AI response must be a JSON object."
        )

    try:
        validated = FinancialInsight.model_validate(raw_data)
    except ValidationError as exc:
        raise ValueError(
            "AI response failed schema validation."
        ) from exc

    return validated.model_dump()


def generate_financial_insight(
        financial_data: dict,
) -> dict:
    data = json.dumps(
        financial_data,
        separators=(",", ":"),
        default=str,
    )

    prompt = f"""
You are CFOx, a financial controller.

Analyze ONLY this verified financial data:

{data}

Return ONLY valid JSON matching this exact structure:

{{
  "summary": "main financial issue",
  "severity": "normal",
  "evidence": [
    "fact from data",
    "fact from data"
  ],
  "impact": "quantified impact if available",
  "recommendations": [
    "practical action",
    "practical action"
  ]
}}

Rules:
- Never invent numbers.
- Never invent causes.
- Evidence must come directly from the data.
- Use severity normal, warning, or critical.
- Keep the response concise.
- Maximum 2 evidence items.
- Maximum 2 recommendations.
- No markdown.
"""

    try:
        response = ollama.chat(
            model=MODEL,
            keep_alive="30m",
            format="json",
            options={
                "num_predict": settings.AI_MAX_TOKENS,
                "temperature": 0,
            },
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

    except Exception:
        logger.exception("AI provider request failed.")

        return _fallback_insight(
            "AI analysis is temporarily unavailable."
        )

    try:
        content = response["message"]["content"]

    except (KeyError, TypeError):
        logger.exception(
            "AI provider returned an unexpected response shape."
        )

        return _fallback_insight(
            "AI analysis returned an invalid response."
        )

    if not isinstance(content, str):
        logger.error("AI provider returned non-string content.")

        return _fallback_insight(
            "AI analysis returned an invalid response."
        )

    try:
        return _parse_and_validate(content)

    except ValueError:
        logger.exception(
            "AI response parsing or validation failed."
        )

        return _fallback_insight(
            "AI analysis returned an invalid structured response."
        )
