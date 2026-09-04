from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass
class ConversationContext:
    messages: list[dict]
    recent_user_questions: list[str]
    recent_cfo_answers: list[str]


def build_conversation_context(history, max_messages: int = 20):
    history = history[-max_messages:]

    return ConversationContext(
        messages=[
            {"role": m.role, "content": m.content}
            for m in history
        ],
        recent_user_questions=[
            m.content for m in history if m.role == "user"
        ][-5:],
        recent_cfo_answers=[
            m.content for m in history if m.role == "assistant"
        ][-5:],
    )


FOLLOW_UP_PHRASES = (
    "that",
    "this",
    "those",
    "these",
    "it",
    "they",
    "them",
    "the problem",
    "the issue",
    "the decline",
    "the increase",
    "the drop",
    "the fall",
    "the previous",
    "above",
    "earlier",
    "before",
    "same",
    "also",
    "what about",
    "how about",
    "why",
    "then",
)


def is_follow_up_question(question: str) -> bool:
    text = question.lower().strip()
    if not text:
        return False

    return any(
        re.search(rf"(?<!\w){re.escape(p)}(?!\w)", text)
        for p in FOLLOW_UP_PHRASES
    )


def build_reasoning_question(question: str, history) -> str:
    context = build_conversation_context(history)

    if not context.messages or not is_follow_up_question(question):
        return question

    lines = ["Conversation context:"]
    for message in context.messages:
        role = "User" if message["role"] == "user" else "CFOx"
        lines.append(f"{role}: {message['content']}")

    lines.extend(("", "Current user question:", question))
    return "\n".join(lines)


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _money(value):
    number = _number(value)
    return "unavailable" if number is None else f"${number:,.2f}"


def _percent(value):
    number = _number(value)
    return "unavailable" if number is None else f"{number:.2f}%"


def build_verified_reasoning_context(tool_name: str, tool_result) -> dict:
    """
    Normalize verified facts into two groups:
      facts          = directly observed values
      relationships  = deterministic relationships between those values

    No values are invented here.
    """
    result = {
        "tool": tool_name,
        "facts": [],
        "relationships": [],
    }

    if not isinstance(tool_result, dict):
        return result

    facts = result["facts"]
    relationships = result["relationships"]

    comparison = tool_result.get("comparison")
    if isinstance(comparison, dict):
        previous = comparison.get("previous_period") or {}
        current = comparison.get("current_period") or {}
        changes = comparison.get("changes") or {}

        if previous.get("revenue") is not None:
            facts.append(
                f"Previous-period revenue: {_money(previous['revenue'])}."
            )
        if current.get("revenue") is not None:
            facts.append(
                f"Current-period revenue: {_money(current['revenue'])}."
            )
        if changes.get("revenue_change") is not None:
            facts.append(
                f"Revenue change: {_money(changes['revenue_change'])}."
            )
        if current.get("failure_rate") is not None:
            facts.append(
                f"Current-period failure rate: "
                f"{_percent(current['failure_rate'])}."
            )
        if changes.get("failure_rate_change_percentage_points") is not None:
            facts.append(
                "Failure-rate change: "
                f"{_number(changes['failure_rate_change_percentage_points']):.2f} "
                "percentage points."
            )

        revenue_change = _number(changes.get("revenue_change"))
        failure_change = _number(
            changes.get("failure_rate_change_percentage_points")
        )

        if revenue_change is not None and failure_change is not None:
            if revenue_change < 0 and failure_change > 0:
                relationships.append(
                    "Observed relationship: revenue declined while "
                    "failure rate increased in the same comparison."
                )
            elif revenue_change > 0 and failure_change < 0:
                relationships.append(
                    "Observed relationship: revenue increased while "
                    "failure rate decreased in the same comparison."
                )

    anomaly = tool_result.get("anomaly")
    if isinstance(anomaly, dict):
        if anomaly.get("score") is not None:
            facts.append(f"Anomaly score: {anomaly['score']}.")

        reasons = anomaly.get("reasons")
        if isinstance(reasons, list):
            for reason in reasons[:5]:
                if isinstance(reason, str) and reason.strip():
                    facts.append(
                        f"Anomaly signal: {reason.strip()}"
                    )

    cashflow = tool_result.get("cashflow")
    if isinstance(cashflow, dict):
        if cashflow.get("risk") is not None:
            facts.append(
                f"Cash-flow risk: {cashflow['risk']}."
            )
        if cashflow.get("risk_score") is not None:
            facts.append(
                f"Cash-flow risk score: {cashflow['risk_score']}."
            )

    payment_methods = tool_result.get("payment_methods")
    if isinstance(payment_methods, dict):
        method_rows = []

        for method in ("upi", "card", "netbanking"):
            data = payment_methods.get(method)
            if not isinstance(data, dict):
                continue

            current = data.get("current_period") or {}
            previous = data.get("previous_period") or {}
            changes = data.get("changes") or {}

            facts.append(
                f"{method}: current revenue="
                f"{_money(current.get('revenue'))}; previous revenue="
                f"{_money(previous.get('revenue'))}; current failure rate="
                f"{_percent(current.get('failure_rate'))}."
            )

            revenue = _number(current.get("revenue"))
            if revenue is not None:
                method_rows.append((method, revenue))

            failure_change = _number(
                changes.get("failure_rate_change_percentage_points")
            )
            if failure_change is not None and failure_change > 0:
                relationships.append(
                    f"Observed payment signal: {method} failure rate "
                    "increased versus its previous period."
                )

        if method_rows:
            method, revenue = max(method_rows, key=lambda row: row[1])
            relationships.append(
                f"Largest current-period revenue contribution among "
                f"available payment methods: {method} ({_money(revenue)})."
            )

    forecast = tool_result.get("forecast")
    if isinstance(forecast, dict):
        if forecast.get("recent_average") is not None:
            facts.append(
                "Recent daily revenue average: "
                f"{_money(forecast['recent_average'])}."
            )

        forecast_rows = forecast.get("forecast")
        if isinstance(forecast_rows, list) and forecast_rows:
            total = sum(
                _number(row.get("predicted_revenue")) or 0
                for row in forecast_rows
                if isinstance(row, dict)
            )
            facts.append(
                "Returned forecast-horizon revenue total: "
                f"{_money(total)}."
            )

    return result


def serialize_reasoning_context(tool_name: str, tool_result) -> str:
    return json.dumps(
        build_verified_reasoning_context(
            tool_name,
            tool_result,
        ),
        separators=(",", ":"),
    )
