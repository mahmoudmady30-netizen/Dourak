# Dourak V112 — Queue Operations Feature Release

This release removes the subscription/entitlement layer from the product for now and keeps the core Dourak product available without plan gating.

## Removed
- Subscription entitlement Cloud Functions.
- Subscription entitlement Firestore rules/document path.
- Subscription feature flag.
- Subscription audit event.

## Added / improved
- Live estimated waiting time based on the queue's remaining service workload and each service duration.
- Queue workload tracking (`waitingWorkMinutes`) so the estimate updates as customers join, cancel, get called, or appointments activate.
- Owner-controlled temporary queue pause: stops new customer queue entries while existing customers continue normally.
- Priority ticket action for owners/staff; priority tickets are considered before normal tickets when calling next.
- Staff assignment per ticket.
- No-show action for a called customer, with customer notification and booking status update.
- Existing postpone/recall/serve flows retained.
- Ownership transfer, multi-branch, staff permissions, App Check, audit logs, analytics, appointments, notifications, PWA and security CI retained.

## Verification
- Application JavaScript syntax: PASS.
- Cloud Functions JavaScript syntax: PASS.
- Unit tests: 45/45 PASS.
- Python QA compile: PASS (existing warning only in `test_qr_join.py`).
- Subscription scan: PASS — no active subscription entitlement implementation remains.
- Firebase Emulator rules suite is configured in CI; it was not locally certified in this environment because the emulator run previously timed out.
