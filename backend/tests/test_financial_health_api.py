def test_financial_health_requires_auth(client):
    response = client.get("/transactions/analytics/financial-health")

    assert response.status_code in (401, 403)


def test_financial_health_endpoint(client, db):
    from app.auth import create_access_token
    from app.models import User

    user = User(
        email="financial-health-test@example.com",
        hashed_password="test-password",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    response = client.get(
        "/transactions/analytics/financial-health",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["payment_method"] == "all"
    assert "health" in body
    assert "supporting_data" in body

    health = body["health"]

    assert isinstance(health["score"], (int, float))
    assert 0 <= health["score"] <= 100

    assert health["status"] in {
        "healthy",
        "stable",
        "at_risk",
        "critical",
    }

    assert "components" in health
    assert "revenue" in health["components"]
    assert "payment_reliability" in health["components"]
    assert "cashflow" in health["components"]
    assert "anomaly" in health["components"]