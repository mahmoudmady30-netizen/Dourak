# Dourak V76 — Persistent Workspace / Last Role Routing

## Scope
Built directly from V75 Google Auth Mobile Fix. This version makes returning authenticated users reopen the last successful Dourak workspace on the same device.

## Behavior
- Firebase Auth LOCAL persistence remains the identity/session source.
- Last role is stored only as a non-sensitive routing preference and is scoped to the Firebase UID.
- Successful authentication records `dourakLastRole`, `dourakLastRoleUid`, and `dourakLastWorkspaceAt`.
- Boot restores a permanent Firebase user directly into the remembered role without showing the role chooser.
- If no valid role hint exists, owner is inferred only from an authoritative Firestore `businesses.ownerId == auth.uid` lookup; otherwise customer is used.
- Cached role from a different UID is ignored.
- Explicit logout clears active session/business cache but preserves the non-sensitive last-role preference so the same account can return to its previous workspace after signing in again.
- Existing V75 Google Popup/Redirect flow is preserved.
- Email/password and password reset flow are preserved.

## Verification
- Inline JavaScript syntax: PASS (all non-empty inline scripts)
- `tests/deep_audit.js`: PASS
- `tests/smoke.js`: PASS
- `tests/v73_auth_rules_audit.js`: PASS
- Targeted V76 static assertions: PASS
- ZIP integrity: PASS

## Limitation
A real Firebase browser session was not available in the build environment, so persistence was verified statically and through the existing application test suite rather than a live multi-reload browser test.
