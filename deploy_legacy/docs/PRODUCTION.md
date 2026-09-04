# CFOx Production Package

## Architecture

Production uses three containers:

1. PostgreSQL — persistent financial data.
2. FastAPI/Uvicorn — authenticated API and CFO intelligence.
3. Nginx — serves the Vite production bundle.

The browser talks to FastAPI through `VITE_API_URL`.

## Environment

Never commit `.env.production` or real secrets.

Generate strong secrets with a password manager or a cryptographically secure
random generator. `AUTH_SECRET_KEY` must be at least 32 characters for CFOx's
release-readiness gate.

## Database migration

Before starting application traffic on a new deployment:

```powershell
docker compose -f docker-compose.production.yml run --rm backend alembic upgrade head
```

Then:

```powershell
docker compose -f docker-compose.production.yml up -d --build
```

## CI

GitHub Actions runs the backend test suite and frontend production build on
pushes and pull requests.

## Scaling note

The current CFOx rate limiter is process-local. A multi-worker or multi-instance
deployment should replace it with shared state such as Redis before horizontal
scaling.

## Reverse proxy / TLS

For internet-facing production, terminate TLS at a managed load balancer or
reverse proxy and expose only HTTPS publicly. Do not expose PostgreSQL publicly.

## Rollback

Keep the previous application image/tag available. If a release fails smoke
tests, stop the new version and restore the previous image, then investigate
before retrying the migration/application rollout.
