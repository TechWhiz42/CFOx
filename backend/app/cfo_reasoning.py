from dataclasses import dataclass


@dataclass
class ConversationContext:
    messages: list[dict]
    recent_user_questions: list[str]
    recent_cfo_answers: list[str]


def build_conversation_context(history, max_messages: int = 20):
    history = history[-max_messages:]

    messages = []

    for message in history:
        messages.append({
            "role": message.role,
            "content": message.content,
        })

    recent_user_questions = [
        message.content
        for message in history
        if message.role == "user"
    ][-5:]

    recent_cfo_answers = [
        message.content
        for message in history
        if message.role == "assistant"
    ][-5:]

    return ConversationContext(
        messages=messages,
        recent_user_questions=recent_user_questions,
        recent_cfo_answers=recent_cfo_answers,
    )

FOLLOW_UP_PHRASES = {
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
}


def is_follow_up_question(question: str) -> bool:
    normalized = question.lower().strip()

    if not normalized:
        return False

    return any(
        phrase in normalized
        for phrase in FOLLOW_UP_PHRASES
    )

def build_reasoning_question(question: str, history):
    context = build_conversation_context(history)

    if not context.messages:
        return question

    if not is_follow_up_question(question):
        return question

    lines = [
        "Conversation context:"
    ]

    for message in context.messages:
        role = "User" if message["role"] == "user" else "CFOx"
        lines.append(
            f"{role}: {message['content']}"
        )

    lines.extend([
        "",
        "Current user question:",
        question,
    ])

    return "\n".join(lines)