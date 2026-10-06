# DOURAK V79 — Authentication Permission / Race Fix

## Root cause addressed
A successful Firebase email/password authentication was followed by a mandatory Firestore `users/{uid}` profile write inside `finishPermanentAuth()`. If that secondary write returned `permission-denied`, the UI caught the error as if authentication itself had failed and left the user at login.

## V79 behavior
- Firebase Authentication success is now committed as the primary login result.
- `finishPermanentAuth()` persists the local routing session and opens the workspace even if the optional profile sync fails.
- Profile sync remains attempted and logged, but is non-blocking.
- Existing Firestore rules, customer/owner routing, Google auth, password reset, queue/display features, and UI are preserved.
- `lastDourakRole` remains only a routing hint; Firebase Auth and Firestore ownership/membership remain authorization sources.

## Important
This fix prevents a profile permission error from blocking login. If Firestore rules are still not deployed in the Firebase Console, other protected operations can still legitimately return permission-denied and must be diagnosed separately.
