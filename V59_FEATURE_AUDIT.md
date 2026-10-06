# Dourak V59 — Queue Display Theme Selector Audit

Base: Dourak V58 Queue Display Apple Glossy + I18N COMPLETE FINAL.

## Changes
- Fixed standalone Classic display URL precedence so the selected standalone design cannot be overwritten by the business's saved default display theme.
- Kept backward compatibility with the old `displayTheme=apple` URL while the visible product name is now **Classic / كلاسيك**.
- Added a professional Queue Display theme dropdown with two display options.
- Added a small color indicator beside each option: dark/teal for the standard display and light/silver for Classic.
- Added selected-state checkmark, hover/focus styling, click-outside close behavior, RTL/LTR-safe layout, and mobile sizing.
- Open/Copy actions now use the selected dropdown option.
- Language switching refreshes the dropdown's selected label.

## Verification
- Inline JavaScript syntax: PASS
- Duplicate named function declarations: PASS
- Inline UI handlers: PASS
- Packaged assets: PASS
- Firestore rules structural audit: PASS
- Package metadata: PASS
- Existing smoke test: PASS
- ZIP integrity: PASS
