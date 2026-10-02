# Dourak V63 Feature Audit

## Queue workflow
- Restored explicit end-service workflow after a ticket is called.
- Added current-customer action bar in Queue List with Recall + End Service.
- Added Recall + End Service together on Owner Home whenever a called ticket exists.
- Added a Firestore fallback lookup so the workflow does not disappear while the realtime listener is settling.
- Call Next still requires the current called ticket to be completed; this prevents silently ending a customer's service.

## Standalone displays
- Every one of the seven standalone layouts now has: Edit (pencil), Open, Copy Link.
- Per-layout settings are stored under `displayLayouts.<layoutKey>` and sync through Firestore.
- Settings are layout-specific: branch Arabic/English name, counter fields, titles, next-ticket count, welcome text, Near Turn details, Classic recent count, and Multi Counter's four counter definitions.
- Standalone rendering consumes the saved per-layout configuration.
- Explicit Fill to Screen control is retained on every standalone display.
- Standalone queue calls continue to trigger chime + speech on the display when its browser audio has been unlocked.

## Verification
- Inline JavaScript syntax: PASS
- Deep audit: PASS
- Smoke tests: PASS
- V62 feature audit: PASS
- All seven display renderer runtime checks: PASS
