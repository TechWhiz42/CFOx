# CFOx

CFOx is an AI finance controller for Razorpay-style merchant payment data. It helps a merchant understand revenue, failed payments, payment-method degradation, cash-flow risk, anomalies, and practical recovery actions from one authenticated dashboard.

Built for the Razorpay AI Buildathon under the **AI Finance Controller / AI Revenue Recovery** direction.

## What It Does

- Ingests payment transactions directly or through a Razorpay webhook.
- Separates each user's financial data behind authenticated access.
- Detects revenue movement, failed-payment spikes, cash-flow risk, and payment-method anomalies.
- Generates deterministic financial health scores and action priorities.
- Uses AI only on top of verified metrics, with guardrails to avoid invented numbers or causes.
- Keeps CFO chat history per user.
- Shows production-readiness work: migrations, health checks, HttpOnly auth cookies, rate limiting, audit logs, backups, smoke tests, and E2E tests.

## Demo Story

A merchant sees revenue weakening and UPI failures rising. CFOx identifies the verified payment signal, explains the business impact, and gives bounded next actions without making unverified claims.

Good demo prompts:

```text
Which payment method is performing worst?
Why did revenue fall?
What is my biggest financial risk?
Show recent failed payments.
Investigate this financial anomaly.
```

## Architecture

```text
React / Vite frontend
        |
        | HttpOnly cookie auth
        v
FastAPI backend
        |
        | SQLAlchemy + Alembic
        v
PostgreSQL
        |
        +-- Razorpay webhook ingestion
        +-- Deterministic analytics engine
        +-- Financial health/action engine
        +-- CFO conversation history
        +-- AI insight layer over verified data
```

## Tech Stack

- Frontend: React, Vite, Playwright
- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic
- Database: PostgreSQL for Docker demo, SQLite for isolated tests
- AI: Ollama-compatible local model by default
- Ops: Docker Compose, Nginx, health checks, smoke scripts, backup/restore scripts

## Local Demo Setup

Copy the production example env and fill in safe local values:

```powershell
Copy-Item .env.production.example .env.production
```

For local demo, these values are expected:

```env
ENVIRONMENT=production
ENABLE_API_DOCS=false
AUTH_COOKIE_SECURE=false
CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:5173
VITE_API_URL=http://localhost:8000
```

Start the stack:

```powershell
docker compose -f docker-compose.production.yml --env-file .env.production up -d --build
```

Seed demo data:

```powershell
docker compose -f docker-compose.production.yml --env-file .env.production exec backend python seed.py
```

Open:

```text
http://localhost
```

Demo login:

```text
Email: demo@cfox.local
Password: StrongPassword123
```

## Development Setup

Backend:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m pytest -q
```

Frontend:

```powershell
cd frontend
npm ci
npm run lint
npm run build
npm run e2e
```

## Verification

Smoke tests:

```powershell
powershell -ExecutionPolicy Bypass -File .\release\scripts\smoke-test.ps1
powershell -ExecutionPolicy Bypass -File .\release\scripts\frontend-smoke.ps1
```

Backup:

```powershell
powershell -ExecutionPolicy Bypass -File .\release\scripts\backup-postgres.ps1
```

## Security And Reliability Highlights

- HttpOnly cookie auth for browser sessions.
- JWT issuer/audience validation.
- Argon2 password hashing.
- Request size limit.
- Rate limiting for auth, AI, and webhook surfaces.
- HMAC verification for Razorpay webhooks.
- Idempotent webhook event tracking.
- User-scoped transaction and conversation queries.
- Database constraints for financial data integrity.
- Safe error responses with request IDs.
- Audit logging for auth, transactions, conversations, and webhooks.

## Known Demo Limitations

- Local demo uses a local/Ollama-compatible AI model; judges can still evaluate deterministic analytics even if AI is unavailable.
- Rate limiting is process-local; Redis should replace it before horizontal scaling.
- Public deployment is intentionally not required for this submission package.
- Razorpay webhooks are implemented for test-mode style payment events and require a configured webhook secret.

## Repository Notes

- Real secrets must stay out of Git.
- `.env.production` and database backups are ignored.
- `deploy_legacy/` and `backend/alembic_legacy/` are retained only as historical cleanup context.
