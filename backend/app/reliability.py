class CFOAIServiceError(Exception):
    """Raised when the CFO AI provider cannot produce a response safely."""


def public_ai_error_detail() -> str:
    return "CFO analysis is temporarily unavailable. Please try again."
