# Dourak V45 — Apple Theme + Performance Audit

## Delivered
- Renamed the old theme to **Classic / كلاسيك**.
- Replaced the previous second theme option with a new **Apple** light theme: bright white surfaces, graphite typography, Apple-inspired blue accents, soft glass navigation, refined forms and spacing.
- Owner theme selector is now directly on the owner home screen; the duplicate theme entry was removed from Place Settings.
- Customer theme selector remains available from the customer header.
- Existing stored `premium` theme preference automatically migrates to `apple`.
- Offer messages from Customer Log now include:
  - Business name
  - Business location/address
  - Google Maps link when coordinates exist
  - A welcome line
  - The exact offer content entered by the owner
  - A closing/welcome-back line
- Business photos are compressed more aggressively and use WebP when the browser supports it, with JPEG fallback. Gallery/logo images also use lazy loading + async decoding.
- Customer business discovery is cache-first and refreshes in the background. Repeated Home navigation within 20 seconds no longer triggers a full Firestore refresh.
- Customer discovery no longer loads every ratings collection just to render the home list; stored rating summary fields are used when available.
- Removed a 4-second logo polling loop and reduced it to a lightweight owner-only safety refresh every 60 seconds.
- Updated build marker to `v45-apple-performance`.

## Automated checks
- Smoke tests: PASS
- Deep audit: PASS
- Feature audit: PASS (18 checks)
- Main embedded JavaScript syntax: PASS
- Cloud Functions JavaScript syntax: PASS
- Duplicate named-function scan: PASS
- Inline handler scan: PASS
- Packaged assets: PASS
- Firestore rules structural audit: PASS
- ZIP integrity: PASS

## Production note
Local/static tests cannot prove real Firebase behavior across multiple physical devices without the deployed Firebase project and real accounts. The package is prepared for deployment and the code paths were statically/deep audited.
