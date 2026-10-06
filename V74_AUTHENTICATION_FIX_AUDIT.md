# Dourak V74 — Authentication Reliability Fix Audit

## Fixes
- Email/password LOGIN never uses `linkWithCredential`, even when an anonymous Firebase bootstrap user is currently present.
- Registration still upgrades an anonymous user in place to preserve the UID when the email is new.
- Registration gracefully falls back to normal email/password sign-in when the email credential already belongs to an existing account.
- Added explicit `auth/credential-already-in-use` messaging.
- Password reset now sends with explicit Action Code Settings pointing back to the current Dourak origin/path.
- Password reset UI message tells the user to check Spam/Junk if needed.
- Google login also falls back to normal sign-in when a Google credential already belongs to an existing account.
- Firebase project/domain configuration remains unchanged.

## Verification
- Inline JavaScript syntax checked with Node.
- Existing deep audit and smoke tests run.
- Static auth-flow assertions run.
- ZIP integrity checked.

## Runtime limitation
No real browser session against Firebase Authentication was available in the build environment, so final email delivery and OAuth popup behavior still require one real-device test against the user's Firebase project.
