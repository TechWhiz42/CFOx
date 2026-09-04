import json

import ollama

MODEL = "gemma3:1b"


def route_question(question: str) -> str:
    """
    Fast deterministic routing.

    This avoids making a second LLM call just to decide
    which financial operation is required.
    """

    if not isinstance(question, str):
        return "none"

    text = question.lower().strip()

    # A verified investigation context is already the result of an earlier
    # deterministic investigation. Do not recursively trigger a tool from
    # the evidence text itself.
    if "verified data:" in text and "use only these verified facts" in text:
        return "none"

    # Check specific transaction queries first.
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

    if any(
            keyword in text
            for keyword in failed_transaction_keywords
    ) or (
            "failed" in text
            and ("payment" in text or "transaction" in text)
    ) or (
            "failure" in text
            and ("payment" in text or "transaction" in text)
    ):
        return "get_failed_transactions"

    # Anomaly analysis must run before payment-method analysis because
    # questions such as "unusual UPI payments" contain both concepts.
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

    # Payment-method analysis.
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

    if any(
            keyword in text
            for keyword in payment_keywords
    ):
        return "compare_payment_methods"

    # Revenue analysis.
    revenue_keywords = [
        "revenue",
        "sales",
        "income",
        "earnings",
        "forecast",
        "forecasted",
        "revenue trend",
    ]

    if any(
            keyword in text
            for keyword in revenue_keywords
    ):
        return "get_revenue_analysis"

    # Cash-flow / risk analysis.
    cashflow_keywords = [
        "cash flow",
        "cashflow",
        "financial risk",
        "biggest risk",
        "risk",
        "liquidity",
        "investigate first",
    ]

    if any(
            keyword in text
            for keyword in cashflow_keywords
    ):
        return "get_cashflow_analysis"

    return "none"


def stream_cfo_answer(
        question: str,
        tool_result=None,
):
    """
    Stream the final CFO answer from Ollama.

    This is the only LLM call in the request path.
    """

    if tool_result is None:
        context = "{}"
    else:
        context = json.dumps(
            tool_result,
            separators=(",", ":"),
        )

    prompt = f"""
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

    response = ollama.chat(
        model=MODEL,
        keep_alive="30m",
        options={
            "num_predict": 120,
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
        content = chunk["message"]["content"]

        if content:
            yield content


def generate_cfo_answer(
        question: str,
        tool_result=None,
) -> str:
    """
    Non-streaming version.

    Kept for compatibility with any existing
    code that still uses generate_cfo_answer().
    """

    answer = ""

    for token in stream_cfo_answer(
            question,
            tool_result,
    ):
        answer += token

    return answer
