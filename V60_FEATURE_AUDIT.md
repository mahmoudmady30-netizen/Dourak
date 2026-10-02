# DOURAK V60 — Queue Display Layout System Audit

Base: Dourak V59 Queue Display Classic Dropdown COMPLETE FINAL

## Implemented

- Added exactly seven Queue Display layouts:
  - QUEUE_SPOTLIGHT
  - QUEUE_MULTI_COUNTER
  - QUEUE_SHOWCASE
  - QUEUE_MINIMAL
  - QUEUE_VERTICAL
  - QUEUE_NEAR_TURN
  - QUEUE_CLASSIC
- Replaced the previous two-option Queue Display selector with a professional dropdown containing a color dot for every layout.
- Added persistent `displayLayout` business setting and layout-specific standalone URL parameter.
- Added live owner-side preview for the selected layout and a full seven-layout preview gallery.
- All layouts consume the same live queue data source in the standalone display.
- Added responsive layout behavior for TV/desktop/tablet/mobile and a dedicated 9:16 Vertical layout.
- Added Showcase advertisement media controls shown only when Showcase is selected.
- Added automatic image compression to WebP before saving to Firestore.
- Added optional direct MP4 video URL for Showcase.
- Added `displayMedia` and `displayLayout` to the Firestore business update allow-list.
- Preserved live queue updates, audio/TTS, fullscreen, promotion speed, and display controls.
- Preserved backward compatibility for legacy `displayTheme=classic/apple` URLs by mapping them to `QUEUE_CLASSIC`.
- New layouts use their own visual system and do not inherit the previous Apple/Glossy display background.
- Current display defaults to `A 000` when there is no active current ticket, avoiding a blank queue-number area or invented live number.

## Verification

- All inline JavaScript blocks: `node --check` PASS.
- `tests/deep_audit.js`: PASS.
- `tests/smoke.js`: PASS.
- Firestore rules structural audit: PASS through deep audit.
- ZIP integrity check required before release.

## Historical audit note

Older version-specific audits may intentionally fail when they look for obsolete V45/V58/V59 markers. The current architecture is audited by the generic deep audit and smoke tests above.
