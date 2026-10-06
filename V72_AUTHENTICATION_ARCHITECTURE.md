# Dourak V72 — Authentication Architecture

## Implemented
- Firebase Authentication is now the source of permanent identity for customer and owner sessions.
- Email/password registration and login are real Firebase Auth operations.
- Password reset uses Firebase Auth email reset.
- Google sign-in uses Firebase Auth popup and can upgrade an anonymous Firebase identity with `linkWithPopup` so the UID/business ownership is preserved.
- Phone authentication is implemented with Firebase PhoneAuthProvider + reCAPTCHA and can upgrade an anonymous identity with `linkWithCredential`.
- Anonymous auth remains only as a compatibility/bootstrap identity; the app no longer treats an anonymous user as a permanent logged-in account.
- New owner business creation is blocked until the owner account is upgraded to a permanent Firebase identity.
- QR/customer flows therefore require a permanent customer identity before taking a queue ticket.
- A small authorization foundation was added to Firestore rules: `permanentAuth()`, `memberOf()`, `hasPermission()`, and `businesses/{businessId}/members/{uid}`.
- Logout clears Dourak session keys only and signs out from Firebase.
- Back/bfcache recovery remains compatible with the permanent auth state.

## Compatibility / migration
Existing businesses created under anonymous Firebase UIDs can be preserved by registering/linking the same browser's anonymous identity with email/password, Google, or phone. This keeps the Firebase UID unchanged.

Existing staff username/passcode records remain a transitional compatibility path. Full staff migration to independent Firebase Auth users requires a trusted backend/Cloud Function using Firebase Admin SDK; a browser must never hold an Admin SDK credential. The membership rules are ready for that migration.

## Verification
- All inline JavaScript blocks: syntax PASS.
- Static checks: authentication functions present, anonymous-to-permanent link paths present, permanent-auth queue gate present, membership rules present.
- Firestore rules structural audit: PASS by syntax/static review.
- ZIP integrity: verified after packaging.

## Production configuration required
Enable Email/Password, Google, and Phone providers in Firebase Authentication. Configure authorized domains. Phone Auth also requires the Firebase reCAPTCHA/Phone configuration to be enabled. These provider switches cannot be safely enabled from the client code itself.
