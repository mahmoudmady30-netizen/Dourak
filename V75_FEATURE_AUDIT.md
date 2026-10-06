# DOURAK V75 — Google Auth Popup/Redirect Reliability

Built from **Dourak V74 Authentication Reliability Fix COMPLETE FINAL**.

### Implemented
- Google login is popup-first.
- Automatic redirect fallback for `auth/popup-blocked`.
- Automatic redirect fallback for unsupported popup environments.
- Anonymous Google account upgrade supports `linkWithRedirect()`.
- Existing Google accounts use normal `signInWithRedirect()` when popup is blocked.
- Redirect result is resolved during boot using `getRedirectResult()` before cached session routing.
- OAuth role/mode survive the redirect using temporary `sessionStorage` only.
- Credential-already-in-use/account-exists errors after anonymous linking switch to normal Google sign-in redirect instead of looping.
- Friendly handling for popup blocked, unsupported environment, and unauthorized domain.
- Cache/build marker updated to V75 so stale browser shell assets are invalidated.
- V74 email/password login and password-reset implementation preserved.

### Verification
- Node syntax check: PASS for all non-empty inline scripts.
- `tests/deep_audit.js`: PASS.
- `tests/smoke.js`: PASS.
- `tests/v73_auth_rules_audit.js`: PASS.
- ZIP integrity: PASS.

### Runtime limitation
A real Google OAuth browser round-trip cannot be executed in the packaging environment. The redirect path is implemented against Firebase's documented v8 compat APIs (`signInWithRedirect`, `linkWithRedirect`, `getRedirectResult`).
