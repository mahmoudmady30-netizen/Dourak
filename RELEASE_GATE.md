# Dourak V108 — Final Release Gate

## Source-level security changes

- [x] Stored XSS dynamic inline-handler issue fixed with `A(...)`.
- [x] Staff permissions enforced in Firestore Rules.
- [x] Queue ticket reads restricted.
- [x] Inactive business reads restricted.
- [x] Ratings privacy restricted.
- [x] Staff passcodes stored as SHA-256 hashes only.
- [x] `staffSecrets` is never client-readable.
- [x] Client-created `staffAuth` disabled.
- [x] Client-created `staffSessions` disabled.
- [x] Staff login moved to App-Check-protected Cloud Function.
- [x] Server-side rate limiting added.
- [x] App Check client SDK initialized with automatic token refresh.

## Required deployment actions

These actions require access to the real Firebase project and cannot be performed by a ZIP archive alone:

1. Configure the production App Check public site key in `index.html`.
2. Register the web app in Firebase App Check.
3. Deploy `functions/`.
4. Deploy `firestore.rules`.
5. Enable Cloud Functions App Check enforcement.
6. Monitor App Check metrics and then enable product enforcement appropriate to the production architecture.
7. Run the emulator and browser tests against the exact release commit.
8. Run two-account authorization tests: Customer A/B, Owner, Queue-only Staff, Services-only Staff, Analytics-only Staff, and deactivated Staff.

A build is not considered production-live until the deployment-side App Check configuration and tests above pass.
