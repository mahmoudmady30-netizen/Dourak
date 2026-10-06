# Dourak V52 — Complete Package Audit

- Base preserved from the complete V50 package, including `functions/` and `tests/`.
- V51 TV audio, human voice selection, audio unlock, and promotion attention behavior preserved in `index.html`.
- V52 adds a dedicated Fit-to-All-Screens layer for TV, tablet, mobile, portrait/landscape, and 720p/1080p/2K/4K viewport classes.
- Display mode uses `100dvh/100vw`, bounded grid rows, hidden overflow, responsive `clamp()` sizing, and reduced-motion handling.
- Firebase config/rules, Cloud Functions, assets, PWA manifest, and audit/test files are included.
- No `localStorage.clear()` or `sessionStorage.clear()` build migration was introduced.

## V53 Display Pro Controls
- Independent queue display now has a professional side control rail.
- Manual display scale: 85%–118%, plus reset; saved per display device.
- Six selectable display themes: Pearl, Ocean, Mint, Sand, Lavender, Graphite.
- Owner can set the default display theme for the business.
- Promotion lock now explicitly writes `enabled:false` and clears the display text, so the live banner is removed immediately from connected displays.
- `displayTheme` is included in the Firestore business update allow-list.
