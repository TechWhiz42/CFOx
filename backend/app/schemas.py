from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
)


# =========================================================
# USER / AUTH
# =========================================================

class UserSignup(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


# =========================================================
# TRANSACTIONS
# =========================================================

SUPPORTED_PAYMENT_METHODS = {
    "upi",
    "card",
    "netbanking",
}

TRANSACTION_STATUSES = {
    "success",
    "failed",
    "refunded",
}


class TransactionCreate(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    """
    Client-controlled transaction fields.

    user_id is intentionally absent.
    Ownership always comes from the authenticated JWT.
    """

    razorpay_payment_id: str = Field(
        min_length=1,
        max_length=255,
    )

    amount: Decimal = Field(
        gt=Decimal("0"),
        max_digits=18,
        decimal_places=2,
    )

    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )

    status: Literal[
        "success",
        "failed",
        "refunded",
    ]

    payment_method: str | None = Field(
        default=None,
        max_length=32,
    )

    customer_id: str | None = Field(
        default=None,
        max_length=255,
    )

    created_at: datetime | None = None

    @field_validator(
        "razorpay_payment_id",
        "currency",
        "customer_id",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value):
        if value is None:
            return value

        if not isinstance(value, str):
            raise ValueError("must be a string")

        return value.strip()

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.upper()

        if value != "INR":
            raise ValueError("currency must be INR")

        return value

    @field_validator("payment_method", mode="before")
    @classmethod
    def normalize_payment_method(cls, value):
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "payment_method must be a string"
            )

        value = value.strip().lower()

        if value not in SUPPORTED_PAYMENT_METHODS:
            raise ValueError(
                "payment_method must be one of: "
                "upi, card, netbanking"
            )

        return value


class TransactionResponse(TransactionCreate):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# =========================================================
# AI FINANCIAL INVESTIGATION
# =========================================================

class AIInvestigationRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
    )

    days: int = Field(
        default=7,
        ge=1,
        le=90,
    )


class AIInvestigationResponse(BaseModel):
    question: str
    investigation_type: str
    period_days: int
    evidence_data: dict
    summary: str
    severity: str
    evidence: list[str]
    impact: str
    recommendations: list[str]


# =========================================================
# PERSISTENT CFO CONVERSATIONS
# =========================================================

class CFOConversationMessageRequest(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=4000,
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Message cannot be empty."
            )

        return value


class CFOConversationMessage(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class CFOConversationCreateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator("title")
    @classmethod
    def normalize_title(
            cls,
            value: str | None,
    ) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value


class CFOConversationResponse(BaseModel):

    id: int
    user_id: int
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class CFOConversationDetailResponse(
    CFOConversationResponse
):
    messages: list[CFOConversationMessage] = Field(
        default_factory=list,
    )


class CFOConversationMessageResponse(BaseModel):

    conversation_id: int
    tool_used: str
    user_message: CFOConversationMessage
    assistant_message: CFOConversationMessage
