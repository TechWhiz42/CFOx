import json
import re

import ollama


MODEL = "gemma3:1b"


# =========================================================
# ROUTING CONFIGURATION
# =========================================================

VERIFIED_CONTEXT_MARKERS = (
    "investigate this detected financial anomaly",
    "verified anomaly score",
    "verified data:",
    "use only these verified facts",
    "use only the verified data",
    "verified alert evidence",
)


FAILED_TRANSACTION_PATTERNS = (
    r"\bfailed transaction(?:s)?\b",
    r"\bfailed payment(?:s)?\b",
    r"\bfailed\s+\w+\s+payment(?:s)?\b",
    r"\bpayment(?:s\s+)?(?:have\s+)?failed\b",
    r"\btransaction(?:s\s+)?(?:have\s+)?failed\b",
    r"\bpayment(?:s)?\s+failure(?:s)?\b",
    r"\btransaction(?:s)?\s+failure(?:s)?\b",
)


ANOMALY_PATTERNS = (
    r"\banomal(?:y|ies)\b",
    r"\banomalous\b",
    r"\bunusual transaction(?:s)?\b",
    r"\bunusual payment(?:s)?\b",
    r"\bsuspicious transaction(?:s)?\b",
    r"\bsuspicious payment(?:s)?\b",
    r"\boutlier(?:s)?\b",
)


PAYMENT_METHOD_PATTERNS = (
    r"\bpayment method(?:s)?\b",
    r"\bpayment performance\b",
    r"\bpayment failure rate\b",
    r"\bwhich payment\b",
    r"\bcompare payment(?:s)?\b",
    r"\bupi\b",
    r"\bnetbanking\b",
    r"\bnet banking\b",
    r"\bcard payment(?:s)?\b",
)


CASHFLOW_PATTERNS = (
    r"\bcash flow\b",
    r"\bcashflow\b",
    r"\bfinancial risk\b",
    r"\bbiggest risk\b",
    r"\bliquidity\b",
    r"\binvestigate first\b",
)


REVENUE_PATTERNS = (
    r"\brevenue\b",
    r"\bsales\b",
    r"\bincome\b",
    r"\bearnings\b",
    r"\bforecast(?:ed)?\b",
    r"\brevenue trend\b",
)


def _contains_pattern(
    text: str,
    patterns: tuple[str, ...],
) -> bool:
    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def _has_verified_context(text: str) -> bool:
    return any(
        marker in text
        for marker in VERIFIED_CONTEXT_MARKERS
    )


def route_question(question: str) -> str:
    """
    Deterministically classify a CFO question.
    """

    if not isinstance(question, str):
        return "none"

    text = question.strip().lower()

    if not text:
        return "none"

    if _has_verified_context(text):
        return "none"

    if _contains_pattern(
        text,
        FAILED_TRANSACTION_PATTERNS,
    ):
        return "get_failed_transactions"

    if _contains_pattern(
        text,
        ANOMALY_PATTERNS,
    ):
        return "get_anomaly_analysis"

    if _contains_pattern(
        text,
        PAYMENT_METHOD_PATTERNS,
    ):
        return "compare_payment_methods"

    if _contains_pattern(
        text,
        CASHFLOW_PATTERNS,
    ):
        return "get_cashflow_analysis"

    if _contains_pattern(
        text,
        REVENUE_PATTERNS,
    ):
        return "get_revenue_analysis"

    return "none"


# =========================================================
# VERIFIED CONTEXT
# =========================================================

def _format_money(value) -> str:
    """
    Format a verified numeric financial value.
    """

    if value is None:
        return "N/A"

    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _build_revenue_context(tool_result: dict) -> str:
    """
    Build a compact, explicit context for revenue analysis.

    The backend calculates the numbers.
    The LLM only explains them.
    """

    current_period = tool_result.get(
        "current_period",
        {},
    )

    previous_period = tool_result.get(
        "previous_period",
        {},
    )

    changes = tool_result.get(
        "changes",
        {},
    )

    forecast = tool_result.get(
        "forecast",
        {},
    )

    total_revenue = current_period.get(
        "total_revenue"
    )

    previous_revenue = previous_period.get(
        "total_revenue"
    )

    revenue_change = changes.get(
        "revenue_change"
    )

    revenue_change_percentage = changes.get(
        "revenue_change_percentage"
    )

    recent_average = forecast.get(
        "recent_average"
    )

    return f"""
CURRENT PERIOD TOTAL REVENUE: {_format_money(total_revenue)}
PREVIOUS PERIOD TOTAL REVENUE: {_format_money(previous_revenue)}
REVENUE CHANGE: {_format_money(revenue_change)}
REVENUE CHANGE PERCENTAGE: {
    f"{float(revenue_change_percentage):.2f}%"
    if revenue_change_percentage is not None
    else "N/A"
}
FORECAST AVERAGE: {_format_money(recent_average)}
""".strip()


def _build_verified_context(tool_result=None) -> str:
    """
    Convert tool output into a compact context suitable
    for the language model.

    Revenue gets an explicit financial summary.
    Other tool outputs remain available as structured data.
    """

    if tool_result is None:
        return "{}"

    if not isinstance(tool_result, dict):
        return str(tool_result)

    # -----------------------------------------------------
    # Revenue analysis
    # -----------------------------------------------------

    if (
        "current_period" in tool_result
        and "previous_period" in tool_result
        and "changes" in tool_result
        and "payment_methods" in tool_result
    ):
        return _build_revenue_context(
            tool_result
        )

    # -----------------------------------------------------
    # Existing verified contexts
    # -----------------------------------------------------

    return json.dumps(
        tool_result,
        separators=(",", ":"),
        default=str,
    )


# =========================================================
# PROMPT
# =========================================================

def _build_cfo_prompt(
    question: str,
    tool_result=None,
) -> str:
    """
    Build the single prompt sent to the CFO model.
    """

    context = _build_verified_context(
        tool_result
    )

    return f"""
You are CFOx, a financial controller.

The backend has already calculated and verified the financial data below.

VERIFIED FINANCIAL FACTS:
{context}

USER QUESTION:
{question}

STRICT RULES:
- Answer the user's question directly.
- Use ONLY the verified financial facts.
- The backend is the source of truth.
- Never invent numbers.
- Never invent transactions.
- Never invent causes.
- Never make up missing financial information.
- Never perform unnecessary calculations yourself.
- When an exact metric is provided, use that exact metric.
- Never confuse current-period values with previous-period values.
- Never confuse total_revenue with revenue_change.
- Never output placeholders or template variables.
- NEVER output strings such as ${{variable}}, {{variable}}, <variable>, or similar placeholders.
- Never output JSON.
- Never expose internal field names such as "revenue_change".
- State the relevant financial fact first.
- Give a short practical recommendation only when supported by the verified data.
- If the requested information is unavailable, explicitly say that the verified data does not contain it.
- Keep the answer under 120 words.
- Return ONLY the final answer to the user.

Write a clear, natural CFO-style response.
""".strip()


# =========================================================
# OLLAMA RESPONSE EXTRACTION
# =========================================================

def _extract_chunk_content(chunk) -> str:
    """
    Extract generated text from both dictionary responses
    and Ollama ChatResponse objects.
    """

    if chunk is None:
        return ""

    if isinstance(chunk, dict):
        message = chunk.get("message")

        if isinstance(message, dict):
            content = message.get(
                "content",
                "",
            )

            if isinstance(content, str):
                return content

        return ""

    message = getattr(
        chunk,
        "message",
        None,
    )

    if message is None:
        return ""

    content = getattr(
        message,
        "content",
        "",
    )

    if isinstance(content, str):
        return content

    return ""


# =========================================================
# STREAMING ANSWER
# =========================================================

def stream_cfo_answer(
    question: str,
    tool_result=None,
):
    """
    Stream the final CFO answer from Ollama.
    """

    prompt = _build_cfo_prompt(
        question,
        tool_result,
    )

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
        content = _extract_chunk_content(
            chunk
        )

        if content:
            yield content


# =========================================================
# NON-STREAMING COMPATIBILITY
# =========================================================

def generate_cfo_answer(
    question: str,
    tool_result=None,
) -> str:
    """
    Generate the CFO answer.

    Deterministic answers are preferred for exact financial
    metrics. Ollama is used for questions requiring reasoning.
    """

    deterministic_answer = _deterministic_cfo_answer(
        question,
        tool_result,
    )

    if deterministic_answer is not None:
        return deterministic_answer

    answer = ""

    for token in stream_cfo_answer(
        question,
        tool_result,
    ):
        answer += token

    return answer.strip()

def _deterministic_cfo_answer(
    question: str,
    tool_result,
) -> str | None:
    """
    Return an exact backend-generated answer for questions
    where the requested financial metric is unambiguous.

    Returns None when the question requires LLM reasoning.
    """

    if not isinstance(tool_result, dict):
        return None

    normalized = question.lower().strip()

    # -----------------------------------------------------
    # Total revenue
    # -----------------------------------------------------

    total_revenue = (
        tool_result
        .get("current_period", {})
        .get("total_revenue")
    )

    if (
        total_revenue is not None
        and "revenue" in normalized
        and (
            "total" in normalized
            or "how much" in normalized
            or "how much revenue" in normalized
            or "what is my revenue" in normalized
        )
    ):
        return (
            f"Your current total revenue is "
            f"${float(total_revenue):,.2f}."
        )

    return None