# Dourak V51 Feature Audit

- Public display audio unlock: improved for TV pointer/touch/keyboard gesture.
- AudioContext resume: guarded and retried.
- Speech voice loading: waits for `voiceschanged` and selects preferred natural system voices when available.
- Arabic voice preference: Google Arabic / Microsoft Hamed / Maged / Hoda / Arabic fallback.
- English voice preference: Microsoft Aria / Jenny / Guy / Google / Samantha / Karen / Alex fallback.
- Speech rate/pitch tuned for a less robotic cadence.
- Chime remains available as a non-speech fallback.
- Display audio button visibly pulses until a user gesture unlocks audio.
- Banner mode now blinks/fades and softly pulses its glow to attract attention while remaining readable.
- Reduced-motion preference disables attention animations.
- Build id: v51-tv-audio-human-voice-banner-attention.

## Validation
- Main inline JavaScript syntax: PASS (`node --check`).
- Required V51 markers present: PASS.
- Archive integrity: PASS (`unzip -t`).
