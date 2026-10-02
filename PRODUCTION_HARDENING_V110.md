# Dourak V110 — Global Production Hardening

This release adds a production-hardening layer on top of V109:

- App Check / reCAPTCHA Enterprise integration remains enabled.
- Staff authentication remains server-side with PBKDF2-SHA256 and App Check enforcement.
- Security event/audit logging is server-side and append-only from the client perspective.
- Feature flags provide safe operational kill-switches without changing authorization.
- Online/offline UX is explicit; destructive queue actions are guarded against duplicate taps.
- PWA install metadata and offline fallback are included.
- Security headers and CSP reporting are configured in Firebase Hosting.
- CI security gate includes syntax, secret-pattern scan, rules sanity, dependency audit and archive integrity.

## Important production controls outside the ZIP

The ZIP cannot create or configure Firebase/Google Cloud infrastructure by itself. Before public launch:

1. Deploy Firestore rules and Cloud Functions.
2. Confirm App Check metrics and then enable enforcement for the required Firebase products.
3. Configure Firestore scheduled backups in Google Cloud/Firebase and perform a restore drill.
4. Enable Firebase/Cloud Logging alerts for function errors and App Check failures.
5. Run two-customer, two-owner, staff-permission, concurrent-queue and offline/reconnect tests against the real project.
