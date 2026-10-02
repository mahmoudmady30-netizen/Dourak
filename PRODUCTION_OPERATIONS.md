# Dourak V110 Production Operations

## Backups
Configure Firestore scheduled backups in Google Cloud/Firebase. Recommended baseline: daily backup with a retention policy appropriate to the business. Perform a restore drill before launch and after major schema changes.

## Monitoring
Create alerts for Cloud Functions errors, permission-denied spikes, App Check failures, and abnormal write volume. Do not send customer message contents or phone numbers to telemetry.

## Ownership recovery
Ownership transfer must be performed through a server-side/admin-reviewed workflow. Never allow a client to change `ownerId` directly. The current Firestore rules preserve the existing ownerId and therefore intentionally do not implement self-service transfer.

## Abuse controls
App Check, Firestore rules, server-side Staff login rate limits, and client duplicate-action guards are layered controls. App Check is not a replacement for authorization or rate limiting.

## Release gate
Before public launch run:
- Customer A cannot read/modify Customer B's tickets/bookings.
- Owner A cannot read/modify Owner B's business.
- Staff permissions are enforced by Firestore rules.
- Concurrent ticket creation produces unique numbers and respects capacity.
- Offline tap does not claim a ticket was confirmed.
- App Check is enforced only after metrics confirm valid traffic.
