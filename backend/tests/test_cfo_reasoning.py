from app.cfo_reasoning import (
    build_conversation_context,
    build_reasoning_question,
    is_follow_up_question,
)


def test_empty_history_returns_original_question():
    question = "Why did revenue fall?"

    result = build_reasoning_question(
        question,
        [],
    )

    assert result == question


def test_follow_up_question_includes_conversation_context():
    history = [
        type(
            "Message",
            (),
            {
                "role": "user",
                "content": "Why did revenue fall?",
            },
        )(),
        type(
            "Message",
            (),
            {
                "role": "assistant",
                "content": (
                    "Revenue fell because successful transactions declined."
                ),
            },
        )(),
    ]

    question = "What about refunds?"

    result = build_reasoning_question(
        question,
        history,
    )

    assert "Why did revenue fall?" in result
    assert "Revenue fell because successful transactions declined." in result
    assert "What about refunds?" in result


def test_independent_question_does_not_include_history():
    history = [
        type(
            "Message",
            (),
            {
                "role": "user",
                "content": "Why did revenue fall?",
            },
        )(),
        type(
            "Message",
            (),
            {
                "role": "assistant",
                "content": "Revenue declined due to fewer successful payments.",
            },
        )(),
    ]

    question = "Show me failed transactions."

    result = build_reasoning_question(
        question,
        history,
    )

    assert result == question


def test_follow_up_question_detection():
    assert is_follow_up_question("What about refunds?")
    assert is_follow_up_question("What about that?")
    assert is_follow_up_question("Why did it happen?")
    assert is_follow_up_question("How about UPI?")
    assert is_follow_up_question("What happened to the decline?")


def test_normal_question_not_detected_as_follow_up():
    assert not is_follow_up_question(
        "Show me my revenue for the last 7 days."
    )


def test_conversation_context_extracts_recent_messages():
    history = [
        type(
            "Message",
            (),
            {
                "role": "user",
                "content": "Question 1",
            },
        )(),
        type(
            "Message",
            (),
            {
                "role": "assistant",
                "content": "Answer 1",
            },
        )(),
        type(
            "Message",
            (),
            {
                "role": "user",
                "content": "Question 2",
            },
        )(),
    ]

    context = build_conversation_context(history)

    assert len(context.messages) == 3

    assert context.messages[0]["role"] == "user"
    assert context.messages[0]["content"] == "Question 1"

    assert context.messages[1]["role"] == "assistant"
    assert context.messages[1]["content"] == "Answer 1"

    assert context.recent_user_questions == [
        "Question 1",
        "Question 2",
    ]

    assert context.recent_cfo_answers == [
        "Answer 1",
    ]


def test_conversation_context_limits_messages():
    history = []

    for i in range(30):
        history.append(
            type(
                "Message",
                (),
                {
                    "role": "user",
                    "content": f"Question {i}",
                },
            )()
        )

    context = build_conversation_context(
        history,
        max_messages=20,
    )

    assert len(context.messages) == 20
    assert context.messages[0]["content"] == "Question 10"
    assert context.messages[-1]["content"] == "Question 29"