from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Iterable

@dataclass(frozen=True)
class ReadinessCheck:
    name: str
    passed: bool
    detail: str

def check_required_environment(environ: dict[str, str] | None = None) -> list[ReadinessCheck]:
    env = os.environ if environ is None else environ
    checks = []
    for name in ("AUTH_SECRET_KEY", "AUTH_ALGORITHM"):
        value = env.get(name, "").strip()
        checks.append(ReadinessCheck(
            f"env:{name}", bool(value), "configured" if value else "missing"
        ))
    secret = env.get("AUTH_SECRET_KEY", "").strip()
    checks.append(ReadinessCheck(
        "env:AUTH_SECRET_KEY_strength",
        len(secret) >= 32,
        "strong enough" if len(secret) >= 32 else "must be at least 32 characters",
    ))
    return checks

def summarize_readiness(checks: Iterable[ReadinessCheck]) -> dict:
    checks = list(checks)
    passed = sum(c.passed for c in checks)
    return {
        "ready": bool(checks) and passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": [
            {"name": c.name, "passed": c.passed, "detail": c.detail}
            for c in checks
        ],
    }

def sanitize_error_message(message: str, max_length: int = 240) -> str:
    return " ".join(str(message).split())[:max_length]
