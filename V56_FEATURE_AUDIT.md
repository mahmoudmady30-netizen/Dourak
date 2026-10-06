# Dourak V56 — Queue Display Cleanup & Fit-to-Screen Audit

## Requested changes
- Removed owner home category **05 — التخصيص / المظهر**.
- Removed the bottom **إعدادات شاشة الطابور** section from **إعدادات المكان**.
- Removed the bottom **المظهر** section from **إعدادات المكان**.
- Removed the Queue Display studio hero/header that showed the TV/studio presentation.
- Independent Queue Display now uses a fixed `100dvh` viewport with a responsive grid and viewport-based typography.
- Legacy saved `displayZoom` values are ignored so an old 85–118% value cannot cause a sudden zoom-out.
- Display controls/tool overlays are hidden/disabled; fit is automatic.
- Main queue number is constrained by `vmin` and the layout uses `minmax(0,1fr)` to prevent the number/card from disappearing on initial load.

## Verification
- HTML parsed successfully.
- Inline JavaScript passed `node --check`.
- Duplicate HTML IDs: none detected.
- Required owner screens and independent display container present.
