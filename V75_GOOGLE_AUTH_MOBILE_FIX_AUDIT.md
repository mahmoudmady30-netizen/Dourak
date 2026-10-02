# DOURAK V75 — Google Authentication Mobile / Popup Reliability Fix

## Scope
Built directly from Dourak V74 Authentication Reliability Fix.

## Changes
- Google login remains popup-first on browsers where popups work.
- `auth/popup-blocked` automatically falls back to `signInWithRedirect()`.
- `auth/operation-not-supported-in-this-environment` also falls back to redirect.
- Anonymous-account Google linking uses `linkWithRedirect()` when the popup is blocked.
- Existing-account Google sign-in uses `signInWithRedirect()` when the popup is blocked.
- `getRedirectResult()` is processed during boot before the cached Dourak session is evaluated.
- Redirect mode and role are stored in `sessionStorage` only for the OAuth round trip, then cleared.
- If anonymous linking returns `credential-already-in-use` / `account-exists-with-different-credential`, the flow switches to normal Google sign-in redirect instead of looping.
- Added user-friendly handling for popup-blocked, unsupported environment, and unauthorized-domain errors.
- Email/password and password-reset flows from V74 remain unchanged.

## Verification
- Inline JavaScript syntax checked with Node.
- Static assertions verify popup fallback, redirect result handling, anonymous link redirect, redirect role persistence, and no regression to email login/reset functions.
- ZIP integrity checked with `unzip -t`.

## Firebase requirement
For redirect auth, the production app domain must be present in Firebase Authentication Authorized domains. Firebase also documents additional redirect setup for browsers that block third-party storage. See official Firebase redirect best practices.
