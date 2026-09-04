# CFOx Product Cleanup Audit

Generated: 2026-09-03T22:40:57

## Scope
- Frontend source consistency and exact-duplicate detection
- Conservative legacy cleanup
- Backend API inventory
- No module is deleted merely because it appears unused

Frontend source files scanned: **51**

## Exact duplicates detected
- None.

## Files removed by this pass
- None.

## Backend API inventory
- `/login` — `backend/app/auth_routes.py`
- `/me` — `backend/app/auth_routes.py`
- `/register` — `backend/app/auth_routes.py`
- `/` — `backend/app/main.py`
- `/ai/investigate` — `backend/app/routes.py`
- `/alerts` — `backend/app/routes.py`
- `/analytics/advanced-kpis` — `backend/app/routes.py`
- `/analytics/ai-insight` — `backend/app/routes.py`
- `/analytics/anomaly` — `backend/app/routes.py`
- `/analytics/cashflow-risk` — `backend/app/routes.py`
- `/analytics/customer-concentration` — `backend/app/routes.py`
- `/analytics/daily-performance` — `backend/app/routes.py`
- `/analytics/daily-revenue` — `backend/app/routes.py`
- `/analytics/financial-actions` — `backend/app/routes.py`
- `/analytics/financial-health` — `backend/app/routes.py`
- `/analytics/payment-methods` — `backend/app/routes.py`
- `/analytics/revenue-forecast` — `backend/app/routes.py`
- `/analytics/revenue-history` — `backend/app/routes.py`
- `/cfo/chat` — `backend/app/routes.py`
- `/cfo/conversations` — `backend/app/routes.py`
- `/cfo/conversations/{conversation_id}` — `backend/app/routes.py`
- `/cfo/conversations/{conversation_id}/messages` — `backend/app/routes.py`
- `/cfo/conversations/{conversation_id}/messages/stream` — `backend/app/routes.py`
- `/dashboard` — `backend/app/routes.py`

## Safety policy
Apparently-unused files are not automatically deleted. CFOx has router
registration, runtime callbacks, streaming paths, and feature-specific
modules, so an import-only heuristic is insufficient evidence for deletion.

## Required validation
Run the complete backend pytest suite and frontend production build after this pass.
