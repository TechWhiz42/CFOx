# CFOx 20C — Release Readiness

This package adds a small, deterministic release gate around the production package.

## Install

From the package directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\preflight.ps1
```

The script checks:

- CFOx directory structure
- production Compose file
- production environment template
- backend/frontend presence
- Docker CLI and daemon
- Compose configuration validity
- backend requirements
- frontend package manifest

It does **not** expose or print secret values.

## Validate Compose

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\validate-compose.ps1
```

## After the stack is running

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke-test.ps1
```

The smoke test checks the frontend and the existing FastAPI `/docs` endpoint.

## Important

20C intentionally does not invent a `/health` API endpoint. If CFOx later gets a dedicated readiness endpoint, the smoke test can be upgraded to use it.

The release gate follows the production principle that container configuration should be validated before deployment and that service readiness should be tested rather than inferred merely from a container being started.
