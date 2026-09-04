import logging

logger = logging.getLogger("cfox.audit")


def audit_event(
        event: str,
        *,
        user_id: int | None = None,
        request_id: str | None = None,
        metadata: dict | None = None,
) -> None:
    safe_metadata = metadata or {}

    logger.info(
        "audit_event event=%s user_id=%s request_id=%s metadata=%s",
        event,
        user_id,
        request_id,
        safe_metadata,
    )