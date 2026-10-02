# Dourak V108 — Production Security Hardening

## Changes applied

1. Replaced dynamic `JSON.stringify(...)` values embedded in single-quoted inline `onclick` attributes with the existing HTML-safe JSON attribute helper `A(...)` to prevent stored DOM/HTML injection through attacker-controlled Firestore IDs.
2. Added server-side Firestore authorization capabilities for staff:
   - queue
   - services
   - staff
   - analytics
   - settings
3. Staff capabilities are enforced in Firestore Rules, not only by the UI.
4. Deactivated staff are prevented from using capability-gated operations even if an old staff session document remains.
5. Queue ticket reads are restricted to the ticket owner or authorized queue/analytics staff instead of every authenticated user.
6. Business reads for inactive businesses are restricted to the owner, staff, or admin.
7. Service management now honors the `services` capability.
8. Staff management now honors the `staff` capability while preserving self-status updates.
9. Ratings are no longer readable by every authenticated user; customer-owned ratings and analytics-authorized business users remain readable.
10. Queue/staff/analytics authorization boundaries were tightened while preserving customer access to the public queue counter.
11. Staff authentication moved to an App-Check-protected Cloud Function; raw passcodes are no longer read by the client.
12. Staff passcodes are stored as SHA-256 hashes only; staffSecrets is not client-readable.
13. Client-controlled staffAuth/staffSessions creation is disabled in Firestore Rules; sessions are issued only by the trusted callable.
14. Server-side per-user and per-staff rate limiting was added for staff login attempts.
15. Firebase App Check client initialization was added with auto-refresh; production requires the Firebase Console reCAPTCHA site key.
16. Existing pure business-logic unit suite passed: 45/45.

## Verification performed

- Inline JavaScript syntax: PASS
- Existing unit suite: PASS (45 passed, 0 failed)
- Unsafe dynamic `onclick` + `JSON.stringify(...)` occurrences: 0
- Firestore rules structural brace balance: PASS

## Release gate / external Firebase configuration

The code now enforces App Check for the staff-login callable. Before deployment, set `DOURAK_APPCHECK_SITE_KEY` in the production configuration to the real Firebase App Check reCAPTCHA v3/Enterprise site key and enable App Check enforcement for the production web app in Firebase Console. A debug token must never be used in production.

The package cannot change Firebase Console enforcement or deploy Cloud Functions from this offline build environment; those are deployment-side controls, not source-code changes.

## Environment-limited checks

The repository contains Playwright/browser-based QA and Firebase Emulator rules tests. The current execution environment does not contain the Playwright Chromium executable, and the Firebase Emulator dependencies were not available locally. Those tests therefore were not falsely reported as passing.

Before public production deployment, run:

- Firebase Emulator Security Rules suite
- Playwright/browser QA suite
- A two-account authorization test (customer A vs customer B)
- Owner vs queue-only staff vs services-only staff vs analytics-only staff
- Deactivated staff session test
- Stored-XSS regression test using a malicious ticket/document ID
- Firebase production rules deployment + post-deploy smoke test

## Release note

This archive is the production security build. The only remaining release-gate actions are deployment-side: configure the real App Check site key, deploy the Functions/Rules, and run the included emulator/browser tests against the exact Firebase project. No source-level plaintext staff credential path remains.
