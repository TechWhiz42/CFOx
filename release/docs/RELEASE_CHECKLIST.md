# CFOx Release Checklist

## Before Build

- [ ] `.env.production` exists on the target machine.
- [ ] `.env.production` is ignored by Git.
- [ ] `.env.production.example` contains placeholders only.
- [ ] Production secrets are rotated and stored securely.
- [ ] `CORS_ORIGINS` matches the target frontend origin.
- [ ] `VITE_API_URL` matches the target backend URL.
- [ ] `ENABLE_API_DOCS=false` for public production.
- [ ] `DEBUG=false`.

## Validation

- [ ] Backend tests pass.

```powershell
cd backend
python -m pytest -q