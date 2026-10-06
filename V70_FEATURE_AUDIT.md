# Dourak V70 — Owner Back/Settings Business Recovery Audit

## Fix
- Hardened owner Settings navigation after browser Back / bfcache restoration.
- `ownerGo('oSettings')` now refreshes the authenticated owner's authoritative business list and repaints Settings.
- `saveSettings()` now refreshes owner businesses before resolving the active business ID, then performs a server-side owner verification with one recovery pass before saving.
- `loadSettingsForm()` hydrates owner business state when the local business context is empty.
- Added `pageshow` recovery for owner/staff sessions restored from the browser back-forward cache.

## Preserved behavior
- Existing Settings save logic, Firestore fields, owner checks, branches, queue workflow, QR flow, display features, live queue counts, and existing rules remain unchanged.
- No new business is deleted or overwritten by the recovery path.
- New-place setup still creates a new business document through `saveBusinessSetup()`.

## Verification
- All 5 inline script blocks: `node --check` PASS
- `tests/deep_audit.js`: PASS
- `tests/smoke.js`: PASS
- Firestore rules structural audit: PASS via deep audit
- ZIP integrity: PASS
