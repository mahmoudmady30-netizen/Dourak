# Dourak V58 Feature Audit

- Base: Dourak V57 Queue Display Desktop Fix COMPLETE FINAL.
- Fixed initial English selection by translating the authentication landing UI and Queue Display owner UI, plus keeping the existing full translation dictionary and runtime language application.
- Added animated promotion speed selector: slow / normal / fast / very fast, persisted in Firestore as `displayPromotion.speed` and applied live to the standalone display.
- Added a second standalone Queue Display variant using an Apple-inspired glossy light visual system. It uses the same realtime queue, waiting list, promotion, speech/audio and fullscreen features.
- Added owner-side design selector with separate open/copy actions for the standard and Apple Glossy display URLs.
- Removed no previously requested V55/V56/V57 Queue Display cleanup items.
- Legacy `displayZoom` remains ignored by runtime fit-to-screen logic.
- Static JS syntax, duplicate-ID and existing deep-audit checks must pass before release.
