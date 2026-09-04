# Hackathon Demo Guide

## Positioning

CFOx is a finance-control workspace for Razorpay merchants. It turns payment records into an explainable CFO view: what changed, which payment rail is hurting, whether cash flow is at risk, and what action should happen next.

## Five-Minute Pitch

### 0:00 - Problem

Merchants do not just need payment data. They need to know when revenue is slipping, why payment reliability changed, and what action is safe to take. Raw dashboards show metrics, but they rarely close the finance-ops loop.

### 0:45 - Product

CFOx gives the merchant a financial control center. It shows revenue, failure rate, payment-method performance, cash-flow risk, anomalies, and CFO-style recommendations.

### 1:30 - Razorpay Relevance

The app ingests Razorpay-style payment events and verifies webhook signatures. Every transaction belongs to a merchant user, and duplicate webhook events are handled idempotently.

### 2:15 - AI Value

The AI does not make financial decisions from thin air. CFOx first computes verified metrics, then asks the model to explain only those facts. If data is insufficient, it says so.

### 3:15 - Reliability Proof

Show:

- HttpOnly login
- Health/readiness endpoints
- Rate limiting
- Audit logs
- Database constraints
- Backup script
- Playwright E2E test

### 4:15 - Demo Walkthrough

1. Login as `demo@cfox.local`.
2. Show the dashboard.
3. Show payment method comparison.
4. Open anomaly and action center.
5. Ask CFOx: `Which payment method is performing worst?`
6. Ask CFOx: `Why did revenue fall?`
7. Show that answers are grounded in verified data.

### 4:55 - Close

CFOx is not another analytics chart. It is a controlled finance agent: verified inputs, bounded reasoning, auditability, and practical next actions for merchants.

## Local Run Commands

```powershell
docker compose -f docker-compose.production.yml --env-file .env.production up -d --build
docker compose -f docker-compose.production.yml --env-file .env.production exec backend python seed.py
```

Open:

```text
http://localhost
```

Demo account:

```text
demo@cfox.local
StrongPassword123
```

## Judge Checklist

- Public repo has no real secrets.
- README explains the problem and run steps.
- Demo video shows the working app.
- Architecture diagram is included.
- Tests and smoke scripts are available.
