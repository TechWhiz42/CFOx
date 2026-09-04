import json

import app.ai_service as ai_service

FINANCIAL_DATA = {
    "payment_method": "upi",
    "previous_period": {
        "revenue": 100000,
        "failure_rate": 4,
    },
    "current_period": {
        "revenue": 90000,
        "failure_rate": 12,
    },
    "changes": {
        "revenue_change": -10,
        "failure_rate_change_percentage_points": 8,
    },
}


def test_valid_ai_response_is_accepted(monkeypatch):
    response = {
        "message": {
            "content": json.dumps(
                {
                    "summary": "Revenue declined while payment failures increased.",
                    "severity": "warning",
                    "evidence": [
                        "Revenue decreased by 10%.",
                        "Failure rate increased from 4% to 12%.",
                    ],
                    "impact": "Lower revenue and higher payment failures may affect collections.",
                    "recommendations": [
                        "Investigate the increase in payment failures.",
                        "Review UPI transaction reliability.",
                    ],
                }
            )
        }
    }

    monkeypatch.setattr(
        ai_service.ollama,
        "chat",
        lambda **kwargs: response,
    )

    result = ai_service.generate_financial_insight(
        FINANCIAL_DATA
    )

    assert result["summary"] == (
        "Revenue declined while payment failures increased."
    )
    assert result["severity"] == "warning"
    assert len(result["evidence"]) == 2
    assert len(result["recommendations"]) == 2


def test_markdown_code_fence_is_accepted(monkeypatch):
    content = """```json
{
    "summary": "Revenue is stable.",
    "severity": "normal",
    "evidence": [
        "Revenue remained stable."
    ],
    "impact": "No significant impact detected.",
    "recommendations": [
        "Continue monitoring performance."
    ]
}
```"""

    monkeypatch.setattr(
        ai_service.ollama,
        "chat",
        lambda **kwargs: {
            "message": {
                "content": content
            }
        },
    )

    result = ai_service.generate_financial_insight(
        FINANCIAL_DATA
    )

    assert result["severity"] == "normal"
    assert result["summary"] == "Revenue is stable."


def test_invalid_json_returns_fallback(monkeypatch):
    monkeypatch.setattr(
        ai_service.ollama,
        "chat",
        lambda **kwargs: {
            "message": {
                "content": "This is not JSON."
            }
        },
    )

    result = ai_service.generate_financial_insight(
        FINANCIAL_DATA
    )

    assert result["severity"] == "normal"
    assert result["summary"] == (
        "Financial insight is temporarily unavailable."
    )
    assert result["evidence"] == []
    assert result["recommendations"] == []


def test_empty_ai_response_returns_fallback(monkeypatch):
    monkeypatch.setattr(
        ai_service.ollama,
        "chat",
        lambda **kwargs: {
            "message": {
                "content": ""
            }
        },
    )

    result = ai_service.generate_financial_insight(
        FINANCIAL_DATA
    )

    assert result["severity"] == "normal"
    assert result["evidence"] == []
    assert result["recommendations"] == []


def test_invalid_severity_returns_fallback(monkeypatch):
    content = json.dumps(
        {
            "summary": "Something happened.",
            "severity": "danger",
            "evidence": [],
            "impact": "",
            "recommendations": [],
        }
    )

    monkeypatch.setattr(
        ai_service.ollama,
        "chat",
        lambda **kwargs: {
            "message": {
                "content": content
            }
        },
    )

    result = ai_service.generate_financial_insight(
        FINANCIAL_DATA
    )

    assert result["severity"] == "normal"
    assert result["summary"] == (
        "Financial insight is temporarily unavailable."
    )


def test_too_many_evidence_items_returns_fallback(monkeypatch):
    content = json.dumps(
        {
            "summary": "Multiple issues detected.",
            "severity": "warning",
            "evidence": [
                "Fact one",
                "Fact two",
                "Fact three",
            ],
            "impact": "",
            "recommendations": [],
        }
    )

    monkeypatch.setattr(
        ai_service.ollama,
        "chat",
        lambda **kwargs: {
            "message": {
                "content": content
            }
        },
    )

    result = ai_service.generate_financial_insight(
        FINANCIAL_DATA
    )

    assert result["severity"] == "normal"
    assert result["evidence"] == []


def test_provider_exception_returns_fallback(monkeypatch):
    def failing_chat(**kwargs):
        raise RuntimeError("OLLAMA INTERNAL ERROR")

    monkeypatch.setattr(
        ai_service.ollama,
        "chat",
        failing_chat,
    )

    result = ai_service.generate_financial_insight(
        FINANCIAL_DATA
    )

    assert result["summary"] == (
        "Financial insight is temporarily unavailable."
    )
    assert result["severity"] == "normal"
    assert result["evidence"] == []
    assert result["recommendations"] == []


def test_missing_message_returns_fallback(monkeypatch):
    monkeypatch.setattr(
        ai_service.ollama,
        "chat",
        lambda **kwargs: {},
    )

    result = ai_service.generate_financial_insight(
        FINANCIAL_DATA
    )

    assert result["severity"] == "normal"
    assert result["evidence"] == []


def test_non_string_content_returns_fallback(monkeypatch):
    monkeypatch.setattr(
        ai_service.ollama,
        "chat",
        lambda **kwargs: {
            "message": {
                "content": {
                    "summary": "invalid"
                }
            }
        },
    )

    result = ai_service.generate_financial_insight(
        FINANCIAL_DATA
    )

    assert result["severity"] == "normal"
    assert result["evidence"] == []


def test_fallback_matches_financial_insight_schema():
    result = ai_service._fallback_insight(
        "test failure"
    )

    validated = ai_service.FinancialInsight.model_validate(
        result
    )

    assert validated.summary == (
        "Financial insight is temporarily unavailable."
    )
    assert validated.severity == "normal"
    assert validated.impact == "test failure"
