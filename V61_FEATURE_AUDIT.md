# DOURAK V61 — Queue Display Stability + Compact Layout Links

Base: Dourak V60 Queue Display 7 Layouts + Showcase Media COMPLETE FINAL

## Changes

- Removed full-size queue screen previews from the owner Queue Display page.
- Replaced them with seven compact, professional layout rows showing name, description, color dot, selected state, Open and Copy Link actions.
- Each Open action generates a standalone `?display=<businessId>&displayLayout=<layout>` URL.
- Copy Link uses the same canonical standalone URL and includes a clipboard fallback.
- Added explicit standalone display theme/fit helpers that were missing in V60. The missing helpers caused a ReferenceError during direct display boot and could send the app back through the normal start/auth flow.
- Moved the entire standalone display bootstrap inside its own error boundary. Display-route boot failures now remain on the display screen instead of clearing the user session and returning to the start page.
- Standalone display no longer depends on legacy owner zoom state; it always uses automatic fit-to-screen.
- Preserved all seven real queue layouts, realtime Firestore data, audio/TTS, fullscreen, promotion speed, Showcase image/video media, and persisted `displayLayout`.

## Verification targets

- All inline JavaScript blocks: node --check PASS.
- No duplicate named function declarations.
- Deep audit PASS.
- Smoke tests PASS.
- ZIP integrity PASS.
