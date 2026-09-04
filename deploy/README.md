# CFOx — 20B Production Package

This chunk packages CFOx for production-style execution without changing the
application's financial logic.

Included:

- FastAPI production Docker image
- Vite + Nginx production image
- PostgreSQL production Compose stack
- Development/CI environment example
- Production environment example
- GitHub Actions backend/frontend CI
- Production architecture and migration guide
- Backup-aware PowerShell installer

## Apply

From the extracted package:

```powershell
cd D:\path	o\extracted\CFOx_20B_Production_Package
powershell -ExecutionPolicy Bypass -File .\scripts_apply_20b.ps1
```

This writes into `D:\CFOx` and backs an existing `backend/app/config.py` before
touching it. The package intentionally does not overwrite your application's
config logic automatically; your existing config has already been validated
against the project.

## Validate current development setup first

```powershell
cd D:\CFOxackend
.\.venv\Scripts\python.exe -m pytest -q
```

```powershell
cd D:\CFOxrontend
npm run build
```

## Production preparation

```powershell
cd D:\CFOx
Copy-Item .env.production.example .env.production
```

Edit `.env.production` and replace every placeholder.

Do not commit it.

## Docker validation

If Docker is installed:

```powershell
cd D:\CFOx
docker compose -f docker-compose.production.yml config
```

That command validates Compose interpolation without starting services.

Then, on a real deployment host:

```powershell
docker compose -f docker-compose.production.yml run --rm backend alembic upgrade head
docker compose -f docker-compose.production.yml up -d --build
```

Do not expose PostgreSQL to the public internet.

## Important scaling note

CFOx's current rate limiter is process-local. Before horizontal/multi-worker
scaling, move throttling state to shared infrastructure such as Redis.
