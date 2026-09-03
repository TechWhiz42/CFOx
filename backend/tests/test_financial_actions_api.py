from app.auth import create_access_token, hash_password
from app.models import User


def create_authenticated_headers(db):
    """
    Create a real test user and return a valid JWT Authorization header.
    """

    user = User(
        email="financial-actions-test@example.com",
        hashed_password=hash_password("test-password"),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    return {
        "Authorization": f"Bearer {token}",
    }


def test_financial_actions_requires_auth(client):
    response = client.get(
        "/transactions/analytics/financial-actions"
    )

    assert response.status_code in (401, 403)


def test_financial_actions_endpoint(
    client,
    db,
):
    headers = create_authenticated_headers(db)

    response = client.get(
        "/transactions/analytics/financial-actions",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["payment_method"] == "all"

    assert "health" in body
    assert "actions" in body
    assert "supporting_data" in body

    health = body["health"]

    assert isinstance(
        health["score"],
        (int, float),
    )

    assert 0 <= health["score"] <= 100

    assert health["status"] in {
        "healthy",
        "stable",
        "at_risk",
        "critical",
    }

    assert "components" in health

    components = health["components"]

    assert "revenue" in components
    assert "payment_reliability" in components
    assert "cashflow" in components
    assert "anomaly" in components

    assert isinstance(
        body["actions"],
        list,
    )

    supporting_data = body["supporting_data"]

    assert "comparison" in supporting_data
    assert "anomaly" in supporting_data
    assert "cashflow" in supporting_data
    assert "forecast" in supporting_data


def test_financial_actions_supports_payment_method(
    client,
    db,
):
    headers = create_authenticated_headers(db)

    response = client.get(
        "/transactions/analytics/financial-actions"
        "?payment_method=upi",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["payment_method"] == "upi"

    assert "health" in body
    assert "actions" in body
    assert "supporting_data" in body

    assert isinstance(
        body["actions"],
        list,
    )


def test_financial_actions_rejects_invalid_payment_method(
    client,
    db,
):
    headers = create_authenticated_headers(db)

    response = client.get(
        "/transactions/analytics/financial-actions"
        "?payment_method=bitcoin",
        headers=headers,
    )

    assert response.status_code == 400

    body = response.json()

    assert "detail" in body