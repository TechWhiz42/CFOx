# CFOx Phase 6 — Transaction/Data Architecture

Phase 6 makes transaction ingestion ownership-safe and validates financial inputs.

## API

`POST /transactions` creates a transaction for the authenticated user. `user_id` is never accepted from the client; it
is derived from the JWT.

`GET /transactions?limit=50&offset=0` returns only the authenticated user's transactions, with a maximum page size of
100.

## Validation

- Amount is a positive Decimal with at most 18 digits and 2 decimal places.
- Currency is currently restricted to INR.
- Payment methods: `upi`, `card`, `netbanking`.
- Statuses: `success`, `failed`, `refunded`.
- Unknown request fields are rejected.
- Duplicate Razorpay payment IDs return HTTP 409.

## Migration

`b81f0f4e2a77_require_transaction_ownership.py` makes `transactions.user_id` non-null. It intentionally aborts if any
unowned rows remain, preventing silent ownership corruption.

Before upgrading a database that may contain legacy unowned rows, assign them to the correct account first and verify:

```sql
SELECT COUNT(*) FROM transactions WHERE user_id IS NULL;
```

The expected result before `alembic upgrade head` is `0`.

## Test-suite compatibility fix

The Phase 6 test fixtures now create and assign a dedicated test owner for direct `Transaction` model inserts. This
matches the production `user_id NOT NULL` invariant.

Transaction API responses keep monetary `Decimal` values serialized as strings (for example `"1499.50"`) so exact
decimal precision is preserved over JSON.
