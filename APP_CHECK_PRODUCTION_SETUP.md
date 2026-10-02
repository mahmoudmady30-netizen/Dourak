# Dourak — App Check Production Setup

The source now initializes Firebase App Check and the staff-login Cloud Function enforces App Check server-side.

## One-time Firebase Console setup

1. Open Firebase Console → project `dourak-98e95` → **Security → App Check**.
2. Register the Dourak Web App.
3. Use reCAPTCHA v3 (or migrate this same client to reCAPTCHA Enterprise) and obtain the **public site key**.
4. Put that public site key into `window.DOURAK_APPCHECK_SITE_KEY` in `index.html`.
5. Do NOT put the reCAPTCHA secret key in the repository.
6. Deploy the Functions and Firestore rules from this release.
7. Monitor App Check metrics before enabling enforcement for existing traffic.
8. Enable App Check enforcement for Cloud Functions. For stronger protection, enable it for the Firebase products Dourak actually uses after confirming legitimate traffic is receiving valid tokens.

## Important

- Never use `FIREBASE_APPCHECK_DEBUG_TOKEN` in production.
- The client site key is public; the reCAPTCHA secret key is not.
- If the site key is missing, Dourak intentionally blocks staff login rather than silently falling back to an insecure authentication path.

## Cloud Functions

The `loginStaff` callable is configured with `enforceAppCheck: true` and performs:

- username lookup
- staff active-state validation
- SHA-256 passcode verification
- per-user rate limiting: 8 attempts / 15 minutes
- per-staff rate limiting: 30 attempts / 15 minutes
- trusted creation of `staffSessions/{uid}`
- trusted staff identity reconciliation

Clients cannot create `staffAuth` or `staffSessions` directly anymore.
