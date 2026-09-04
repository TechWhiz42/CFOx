# CFOx Phase 8 — Razorpay Webhook Ingestion

Phase 8 moves transaction ingestion from a manual frontend form toward server-to-server payment events.

## What changed

- Public `POST /webhooks/razorpay` endpoint.
- HMAC-SHA256 verification against the **raw request body**.
- `x-razorpay-event-id` idempotency protection.
- `payment.captured` creates/updates a transaction as `success`.
- `payment.failed` creates/updates a transaction as `failed`.
- A later successful capture can recover a previous failed payment event.
- Webhook-created transactions get their owner from `RAZORPAY_WEBHOOK_USER_ID`, never from request data.
- Webhook event IDs are persisted to prevent duplicate processing.

Razorpay explicitly recommends validating `X-Razorpay-Signature` with HMAC-SHA256 over the unmodified request body and
using `x-razorpay-event-id` for duplicate detection.

## Configuration

Set:

```env
RAZORPAY_WEBHOOK_SECRET=your-webhook-secret
RAZORPAY_WEBHOOK_USER_ID=4
```

The owner ID is intentionally server-side. For the current single-merchant CFOx deployment, all Razorpay events belong
to that configured merchant user. A future multi-merchant version should map Razorpay `account_id` to a CFOx user
instead.

## Migration

```powershell
alembic upgrade head
```

## Local webhook test

Create a JSON payload, compute its HMAC-SHA256 signature with the configured webhook secret, and send:

```text
POST http://127.0.0.1:8000/webhooks/razorpay
X-Razorpay-Signature: <hex-hmac>
x-razorpay-event-id: evt_test_001
Content-Type: application/json
```

The endpoint deliberately does not use the normal JWT dependency because Razorpay cannot authenticate with a CFOx user
token. Its authentication mechanism is the Razorpay signature.
