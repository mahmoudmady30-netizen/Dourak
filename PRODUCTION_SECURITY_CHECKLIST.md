# Dourak Production Security Checklist

## Implemented in this release
- reCAPTCHA Enterprise App Check provider with token auto-refresh.
- App Check enforced on sensitive callable functions.
- Staff passcodes use PBKDF2-SHA256 with random 128-bit salt and 310,000 iterations.
- Legacy SHA-256 staff credentials migrate after successful server-side login.
- Staff login has per-user and per-staff rate limits.
- Staff session creation is server-only.
- Staff capabilities are enforced in Firestore Rules.
- Audit log is server-written and client read-only.
- Security headers are configured in Firebase Hosting.
- CSP is shipped in Report-Only mode to avoid breaking existing inline UI; migrate inline handlers to event listeners before switching to enforcing CSP.
- Queue/booking UI has in-flight duplicate-submit guards.
- Storage is default-deny until a server-validated storage path is introduced.
- CI security gate includes syntax, rules sanity, secret scan, dependency audit and QA checks.

## Required console actions before public launch
1. Confirm the registered reCAPTCHA Enterprise key is for `mahmoudmady30-netizen.github.io` and has no localhost production entry.
2. Keep App Check TTL at 1 hour and monitor metrics.
3. Enable App Check enforcement for Cloud Functions, then Firestore/Storage only after legitimate traffic is confirmed.
4. Deploy Firestore rules, Storage rules and Cloud Functions from the same release.
5. Configure scheduled Firestore exports/backups in Google Cloud and test one restore.
6. Enable Firebase/Google Cloud error monitoring and alerting for Cloud Functions and Firestore.
7. Run two-user authorization tests: Customer A/B, Owner A/B, Staff with each permission combination.
8. Run a race test with concurrent ticket creation and booking attempts.
9. Verify production domain, HTTPS, headers and CSP reports.

## Important limitation
No source-code bundle can prove that the live Firebase project, App Check enforcement, backups, IAM, quotas, billing limits, and production deployment are correctly configured. Those are environment-level release gates and must be verified in the actual Firebase/Google Cloud project.
