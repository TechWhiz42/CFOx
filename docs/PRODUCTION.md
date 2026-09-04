# CFOx Production Runbook

## Architecture

CFOx production runs three main services:

- PostgreSQL for persistent financial data
- FastAPI/Uvicorn for the authenticated API
- Nginx for the Vite frontend bundle

Docker Compose also includes a one-shot `migrate` service that runs Alembic before the backend starts.

## Required Environment

Create `.env.production` from `.env.production.example`.

Never commit `.env.production`.

Required values:

```env
POSTGRES_DB=cfox
POSTGRES_USER=cfox
POSTGRES_PASSWORD=replace-me

AUTH_SECRET_KEY=replace-me
AUTH_ALGORITHM=HS256
AUTH_ISSUER=cfox-api
AUTH_AUDIENCE=cfox-web
AUTH_ACCESS_TOKEN_EXPIRE_MINUTES=60

RAZORPAY_WEBHOOK_SECRET=replace-me
RAZORPAY_KEY_SECRET=replace-me
RAZORPAY_WEBHOOK_USER_ID=1

DEBUG=false
ENVIRONMENT=production
ENABLE_API_DOCS=false
LOG_LEVEL=INFO

AI_MODEL=gemma3:1b
AI_REQUEST_TIMEOUT_SECONDS=60
AI_MAX_TOKENS=120

CORS_ORIGINS=http://localhost,http://localhost:80,http://localhost:5173
VITE_API_URL=http://localhost:8000