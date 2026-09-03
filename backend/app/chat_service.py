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
    r"\bpayment(?:s)?\s+(?:have\s+)?failed\b",
    r"\btransaction(?:s)?\s+(?:have\s+)?failed\b",
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
    """
    Return True when any routing pattern matches.
    """

    return any(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        for pattern in patterns
    )


def _has_verified_context(text: str) -> bool:
    """
    Detect investigation prompts that already contain
    verified financial evidence.

    These requests must not trigger another analytics
    operation, because doing so could replace the supplied
    evidence with unrelated aggregate data.
    """

    return any(
        marker in text
        for marker in VERIFIED_CONTEXT_MARKERS
    )


def route_question(question: str) -> str:
    """
    Deterministically classify a CFO question.

    The router intentionally does NOT use an LLM.

    Priority is based on specificity:

        verified context
            ↓
        failed transactions
            ↓
        anomalies
            ↓
        payment methods
            ↓
        cash flow / risk
            ↓
        revenue
            ↓
        none

    Returning "none" means no additional financial tool
    should be executed.
    """

    if not isinstance(question, str):
        return "none"

    text = question.strip().lower()

    if not text:
        return "none"

    # -----------------------------------------------------
    # VERIFIED CONTEXT
    # -----------------------------------------------------
    #
    # The UI may already provide verified evidence.
    # Never replace that evidence with another aggregate
    # analytics query.
    #
    if _has_verified_context(text):
        return "none"

    # -----------------------------------------------------
    # FAILED TRANSACTIONS
    # -----------------------------------------------------
    #
    # These are highly specific operational questions.
    #
    if _contains_pattern(
        text,
        FAILED_TRANSACTION_PATTERNS,
    ):
        return "get_failed_transactions"

    # -----------------------------------------------------
    # ANOMALY
    # -----------------------------------------------------
    #
    # Anomaly questions should be handled separately from
    # general payment-method performance.
    #
    if _contains_pattern(
        text,
        ANOMALY_PATTERNS,
    ):
        return "get_anomaly_analysis"

    # -----------------------------------------------------
    # PAYMENT METHODS
    # -----------------------------------------------------
    #
    # This covers UPI/card/netbanking comparisons and
    # payment-method performance.
    #
    if _contains_pattern(
        text,
        PAYMENT_METHOD_PATTERNS,
    ):
        return "compare_payment_methods"

    # -----------------------------------------------------
    # CASH FLOW / FINANCIAL RISK
    # -----------------------------------------------------
    #
    if _contains_pattern(
        text,
        CASHFLOW_PATTERNS,
    ):
        return "get_cashflow_analysis"

    # -----------------------------------------------------
    # REVENUE
    # -----------------------------------------------------
    #
    if _contains_pattern(
        text,
        REVENUE_PATTERNS,
    ):
        return "get_revenue_analysis"

    # -----------------------------------------------------
    # GENERAL / UNKNOWN
    # -----------------------------------------------------

    return "none"


def _build_cfo_prompt(
    question: str,
    tool_result=None,
) -> str:
    """
    Build the single prompt sent to the CFO model.
    """

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
""".strip()


def stream_cfo_answer(
    question: str,
    tool_result=None,
):
    """
    Stream the final CFO answer from Ollama.

    This is the only LLM call in the request path.
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
        if not isinstance(chunk, dict):
            continue

        message = chunk.get("message")

        if not isinstance(message, dict):
            continue

        content = message.get("content", "")

        if content:
            yield content


def generate_cfo_answer(
    question: str,
    tool_result=None,
) -> str:
    """
    Non-streaming compatibility wrapper.
    """

    answer = ""

    for token in stream_cfo_answer(
        question,
        tool_result,
    ):
        answer += token

    return answer