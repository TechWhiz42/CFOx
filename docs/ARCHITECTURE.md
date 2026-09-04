# CFOx Architecture

## System View

```text
Browser
  |
  | React/Vite app
  | HttpOnly auth cookie
  v
Nginx frontend container
  |
  v
FastAPI backend container
  |
  +--> PostgreSQL
  +--> Razorpay webhook processor
  +--> Analytics modules
  +--> CFO conversation service
  +--> AI provider adapter
```

## Request Flow

1. A user registers or logs in through `/auth`.
2. The backend sets an HttpOnly `cfox_access_token` cookie.
3. Frontend requests include `credentials: "include"`.
4. Backend resolves the current user from the cookie or legacy Bearer token support.
5. Financial endpoints query only rows owned by that user.
6. Analytics are computed deterministically before any AI response is generated.

## Razorpay Webhook Flow

```text
Razorpay event
  |
  | HMAC-SHA256 signature
  v
/webhooks/razorpay
  |
  +--> verify signature
  +--> require event id
  +--> store event id for idempotency
  +--> create/update transaction for configured owner
```

Webhook ownership comes from server configuration, not from the request body. That keeps the demo single-merchant model simple and prevents a webhook payload from choosing its own user.

## AI Safety Model

The AI layer receives verified financial data only. Prompts instruct the model not to invent numbers, transactions, or causes. Structured insight responses are parsed and validated before returning to the frontend. If the AI provider fails, CFOx returns safe fallback messaging.

## Production Envelope

- Health: `/healthz`
- Readiness: `/readyz`
- Migrations: one-shot Compose `migrate` service
- Auth: HttpOnly cookie, JWT issuer/audience, Argon2
- Limits: request body limit and process-local rate limiting
- Data integrity: Alembic migrations and database check constraints
- Recovery: Postgres backup, restore, and rotation scripts
- Verification: backend tests, frontend build/lint, Playwright E2E, smoke scripts
