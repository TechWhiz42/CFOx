# CFOx Backend

## Authentication boundary

- `/auth/register` and `/auth/login` are public.
- `/auth/login` sets an HttpOnly `cfox_access_token` cookie.
- `/auth/me` accepts the auth cookie and also supports Bearer tokens for tests/compatibility.
- Every `/transactions/*` endpoint requires a valid active user.
- Passwords are hashed with Argon2 through `pwdlib`.
- Access tokens are signed JWTs with issuer and audience validation.

## Local setup

1. Copy `.env.example` to `.env`.
2. Set `DATABASE_URL`.
3. Generate a strong `AUTH_SECRET_KEY`.
4. Start the API from this directory:

```powershell
uvicorn app.main:app --reload
```

## Tests

```powershell
pytest -q
```

The test suite uses an isolated SQLite database and a test JWT secret.

## Demo seed

With the production Compose stack running:

```powershell
docker compose -f ..\docker-compose.production.yml --env-file ..\.env.production exec backend python seed.py
```

Demo credentials:

```text
demo@cfox.local
StrongPassword123
```
