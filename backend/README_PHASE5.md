# CFOx Phase 5 — Transaction Ownership Isolation

This build scopes authenticated transaction analytics to the `user_id` in the JWT.

## What changed

- Added nullable `transactions.user_id` foreign key to `users.id`.
- Added an index on `transactions.user_id`.
- Every authenticated transaction analytics route resolves the current user and passes `current_user.id` into the
  analytics/service layer.
- Analytics, forecasting, revenue history, cash-flow, alerts, and CFO chat tool queries apply the user scope.
- Legacy transactions are never exposed to authenticated users while their `user_id` is NULL.
- The migration automatically assigns legacy transactions to the only existing user when exactly one user exists. If
  multiple users already exist, ambiguous legacy rows remain unowned and require explicit assignment.
- Added API tests covering cross-user isolation and legacy unowned-row isolation.

## Migration

Run:

```powershell
alembic upgrade head
```

Before production, review any legacy transactions left with `user_id IS NULL` and assign them to the correct account
using an explicit data migration or administrative workflow. Do not assign ambiguous data automatically.

## Verification

The source was syntax-compiled successfully. The local execution environment used while packaging this build does not
have the backend runtime dependencies installed, so the full pytest suite was not re-run here. Run locally:

```powershell
pip install -r requirements.txt
pytest -q
```

The previous authenticated build had 55 tests; this build adds two ownership-isolation tests, so the expected suite size
is 57.
