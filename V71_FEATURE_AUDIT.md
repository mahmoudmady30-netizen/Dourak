# Dourak V71 — Expert Stability Review / Settings Context Hardening

## Fixed
- Prevented the Settings screen from painting an empty/stale form while owner business context is still being recovered after browser Back/bfcache or rapid navigation.
- Added a single-flight `ensureOwnerSettingsContext()` recovery gate so concurrent Settings loads do not race each other or overwrite valid state with an empty setup.
- Preserved the existing authoritative Firestore owner verification before Settings writes.
- Preserved V70 QR auto-join, live queue counts, queue workflow, display/immersive modes, Showcase media, Near Turn, and in-store customer workflow.

## Expert review findings
- V62 feature-audit assertion for a "current-ticket guard" is obsolete by design because V65 changed `callNext()` to auto-finish the current customer before calling the next one.
- No duplicate named JS functions or duplicate DOM IDs were found.
- Inline JavaScript syntax, deep architecture audit, smoke tests, and ZIP integrity pass.
- The current demo authentication/rules model still has production-security limitations (notably demo OTP/admin role bootstrap and broad authenticated reads). These were not silently redesigned because doing so would change the existing authentication contract; production deployment should move staff/admin authorization to Firebase Authentication/custom claims or trusted backend code.
