# CFOx Backend

## Authentication boundary

- `/auth/register` and `/auth/login` are public.
- `/auth/me` requires a Bearer access token.
- Every `/transactions/*` endpoint requires a valid active user.
- Passwords are hashed with Argon2 through `pwdlib`.
- Access tokens are signed JWTs.

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
