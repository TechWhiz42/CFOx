import json
import logging

import ollama

from app.config import settings
from app.reliability import CFOAIServiceError

logger = logging.getLogger("cfox.chat")

MODEL = settings.AI_MODEL


def route_question(question: str) -> str:
    if not isinstance(question, str):
        return "none"

    text = question.lower().strip()

    if "verified data:" in text and "use only these verified facts" in text:
        return "none"

    failed_transaction_keywords = [
        "failed transaction",
        "failed transactions",
        "failed payment",
        "failed payments",
        "payment failed",
        "payments failed",
        "transaction failed",
        "transactions failed",
    ]

    if any(keyword in text for keyword in failed_transaction_keywords) or (
            "failed" in text and ("payment" in text or "transaction" in text)
    ) or (
            "failure" in text and ("payment" in text or "transaction" in text)
    ):
        return "get_failed_transactions"

    anomaly_keywords = [
        "anomaly",
        "anomalies",
        "unusual transaction",
        "unusual transactions",
        "unusual payment",
        "unusual payments",
        "suspicious transaction",
        "suspicious transactions",
        "suspicious payment",
        "suspicious payments",
    ]

    if any(keyword in text for keyword in anomaly_keywords):
        return "get_anomaly_analysis"

    payment_keywords = [
        "payment method",
        "payment methods",
        "upi",
        "card",
        "netbanking",
        "net banking",
        "payment performance",
        "payment failure rate",
        "which payment",
        "compare payments",
    ]

    if any(keyword in text for keyword in payment_keywords):
        return "compare_payment_methods"

    revenue_keywords = [
        "revenue",
        "sales",
        "income",
        "earnings",
        "forecast",
        "forecasted",
        "revenue trend",
    ]

    if any(keyword in text for keyword in revenue_keywords):
        return "get_revenue_analysis"

    cashflow_keywords = [
        "cash flow",
        "cashflow",
        "financial risk",
        "biggest risk",
        "risk",
        "liquidity",
        "investigate first",
    ]

    if any(keyword in text for keyword in cashflow_keywords):
        return "get_cashflow_analysis"

    return "none"


def _build_prompt(
        question: str,
        tool_result=None,
) -> str:
    if tool_result is None:
        context = "{}"
    else:
        context = json.dumps(
            tool_result,
            separators=(",", ":"),
            default=str,
        )

    return f"""
You are CFOx, a financial controller.

Verified financial data:
{context}

Question:
{question}

Rules:
- Use ONLY the verified data.
- Never invent numbers.
- Never invent transactions.
- Never invent causes.
- State facts first.
- Give a practical recommendation if useful.
- If the data is insufficient, say so.
- Keep the answer under 120 words.
"""


def stream_cfo_answer(
        question: str,
        tool_result=None,
):
    prompt = _build_prompt(
        question,
        tool_result,
    )

    try:
        response = ollama.chat(
            model=MODEL,
            keep_alive="30m",
            options={
                "num_predict": settings.AI_MAX_TOKENS,
            },
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            stream=True,
        )

        for chunk in response:
            try:
                content = chunk["message"]["content"]
            except (KeyError, TypeError) as exc:
                raise CFOAIServiceError(
                    "AI provider returned invalid stream data."
                ) from exc

            if content:
                yield content

    except CFOAIServiceError:
        raise

    except Exception as exc:
        logger.exception("Streaming AI provider request failed.")

        raise CFOAIServiceError(
            "AI provider request failed."
        ) from exc


def generate_cfo_answer(
        question: str,
        tool_result=None,
) -> str:
    return "".join(
        stream_cfo_answer(
            question,
            tool_result,
        )
    )
