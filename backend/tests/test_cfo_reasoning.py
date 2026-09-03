from app.auth import create_access_token, hash_password
from app.models import ChatMessage, Conversation, User


def authenticated_headers(user):
    token = create_access_token(user.id)

    return {
        "Authorization": f"Bearer {token}",
    }


def create_user(db, email):
    user = User(
        email=email,
        hashed_password=hash_password(
            "StrongPassword123"
        ),
        is_active=1,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def test_conversation_crud_requires_authentication(client):
    response = client.get(
        "/transactions/cfo/conversations"
    )

    assert response.status_code == 401


def test_create_list_and_get_conversation(client, db):
    user = create_user(
        db,
        "conversation-owner@example.com",
    )

    headers = authenticated_headers(user)

    create_response = client.post(
        "/transactions/cfo/conversations",
        json={
            "title": "Revenue investigation",
        },
        headers=headers,
    )

    assert create_response.status_code == 201

    conversation = create_response.json()

    assert conversation["user_id"] == user.id
    assert conversation["title"] == "Revenue investigation"

    conversation_id = conversation["id"]

    list_response = client.get(
        "/transactions/cfo/conversations",
        headers=headers,
    )

    assert list_response.status_code == 200

    items = list_response.json()

    assert len(items) == 1
    assert items[0]["id"] == conversation_id

    db.add(
        ChatMessage(
            conversation_id=conversation_id,
            role="user",
            content="Why did revenue fall?",
        )
    )
    db.commit()

    detail_response = client.get(
        f"/transactions/cfo/conversations/{conversation_id}",
        headers=headers,
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    assert detail["id"] == conversation_id
    assert len(detail["messages"]) == 1
    assert detail["messages"][0]["content"] == (
        "Why did revenue fall?"
    )


def test_conversations_are_isolated_between_users(client, db):
    owner = create_user(
        db,
        "owner@example.com",
    )

    other_user = create_user(
        db,
        "other@example.com",
    )

    owner_headers = authenticated_headers(owner)
    other_headers = authenticated_headers(other_user)

    create_response = client.post(
        "/transactions/cfo/conversations",
        json={
            "title": "Private CFO conversation",
        },
        headers=owner_headers,
    )

    assert create_response.status_code == 201

    conversation_id = create_response.json()["id"]

    list_response = client.get(
        "/transactions/cfo/conversations",
        headers=other_headers,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

    detail_response = client.get(
        f"/transactions/cfo/conversations/{conversation_id}",
        headers=other_headers,
    )

    assert detail_response.status_code == 404

    delete_response = client.delete(
        f"/transactions/cfo/conversations/{conversation_id}",
        headers=other_headers,
    )

    assert delete_response.status_code == 404


def test_delete_conversation_cascades_messages(client, db):
    user = create_user(
        db,
        "delete-owner@example.com",
    )

    headers = authenticated_headers(user)

    create_response = client.post(
        "/transactions/cfo/conversations",
        json={
            "title": "Delete me",
        },
        headers=headers,
    )

    conversation_id = create_response.json()["id"]

    db.add(
        ChatMessage(
            conversation_id=conversation_id,
            role="user",
            content="Temporary question",
        )
    )
    db.commit()

    response = client.delete(
        f"/transactions/cfo/conversations/{conversation_id}",
        headers=headers,
    )

    assert response.status_code == 204

    assert (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id
        )
        .first()
        is None
    )

    assert (
        db.query(ChatMessage)
        .filter(
            ChatMessage.conversation_id ==
            conversation_id
        )
        .count()
        == 0
    )


def test_message_endpoint_persists_exchange(
    client,
    db,
    monkeypatch,
):
    user = create_user(
        db,
        "message-owner@example.com",
    )

    headers = authenticated_headers(user)

    create_response = client.post(
        "/transactions/cfo/conversations",
        headers=headers,
    )

    conversation_id = create_response.json()["id"]

    from app import cfo_conversation_service

    def fake_answer(
        db,
        question,
        history,
        user_id,
    ):
        assert user_id == user.id
        return (
            "get_revenue_analysis",
            "Revenue is stable.",
        )

    monkeypatch.setattr(
        cfo_conversation_service,
        "generate_stateful_cfo_answer",
        fake_answer,
    )

    response = client.post(
        f"/transactions/cfo/conversations/{conversation_id}/messages",
        json={
            "content": "Why did revenue change?"
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["conversation_id"] == conversation_id
    assert data["tool_used"] == "get_revenue_analysis"
    assert data["user_message"]["role"] == "user"
    assert data["assistant_message"]["role"] == "assistant"
    assert data["assistant_message"]["content"] == (
        "Revenue is stable."
    )
