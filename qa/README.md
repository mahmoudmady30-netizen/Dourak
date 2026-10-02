# Dourak QA test suites

Re-run after any change (Python 3 + Playwright/Chromium, Node 18+):

```bash
python3 qa/extract_units.py && node qa/unit_tests.js   # 45 business-logic unit tests
python3 qa/test_ui_smoke_responsive.py                 # 18 screens x 4 widths: runtime errors + overflow
python3 qa/test_tv_audio.py                            # TV audio engine: dedupe, recall, no-speech, stub
python3 qa/test_install_popups.py                      # install flow per platform + popup fallbacks
python3 qa/test_voice_recorder_e2e.py                  # recorder -> WAV -> (mock) Firestore -> TV playback
python3 qa/test_otp_pii.py                             # OTP + customer-data security vs rule-enforcing mock (19 checks)
python3 qa/test_cancel_abuse.py                        # cancellation limit, warnings, lockout, 24h expiry, attacks (16 checks)
python3 qa/test_auth_flows.py                          # session persistence, Google redirect, reset mode (12 checks)
python3 qa/test_google_ios.py                          # Google sign-in on iPhone via GIS + fallbacks (10 checks)
python3 qa/test_voice_preset.py                        # ready-made voice preset: writes + TV playback (6 checks)
python3 qa/test_voice_dialect_dropdown.py              # dialect dropdown: Egyptian/Khaleeji/MSA/English (11 checks)
python3 qa/test_sound_decouple.py                      # phone mute never silences the TV screen (7 checks)
python3 qa/test_google_stuck_recovery.py               # Google sign-in origin_mismatch dead-end recovery (7 checks)
python3 qa/test_role_reconciliation.py                 # owner/customer cross-account safety net (6 checks)
python3 qa/test_qr_join.py                             # QR scan -> booking, logged-in + logged-out + onboarding (9 checks)
python3 qa/test_logout_clears_profile.py               # logout actually clears all customer identity data (6 checks)
python3 qa/test_guest_profile_button.py                # guest-mode account screen shows login, not logout (7 checks)
```
See QA_REPORT.md in the project root for the full findings.

python3 qa/test_owner_header_contrast.py              # owner header WCAG contrast, 2 themes x light/dark x button state (8 checks)
python3 qa/test_app_contrast.py                        # every text element, 18 screens, 2 themes x light/dark, WCAG 4.5:1 (4 checks)
python3 qa/test_queue_badge_clears.py                  # دوري badge clears when the turn ends, incl. start-up race + stale tickets (10 checks)
python3 qa/_contrast_scan.py apple dark -v -w          # diagnostic: list every failing/weak text element with the surface behind it
python3 qa/test_security_write_shapes.py              # app writes match what the V107 rules require (21 checks)
# qa/rules/rules.test.mjs — real Firestore emulator tests; run automatically by GitHub Actions (cd qa/rules && npm install && npm test)
