# Dourak V64 Feature Audit

- Fixed Firestore permission failure when saving Queue Display layout settings by allowing the business `displayLayouts` field in owner updates.
- Queue Display layout editor now persists the complete `displayLayouts` map safely.
- Showcase editor includes advertisement media controls directly inside the Showcase edit popup.
- Image uploads are aggressively compressed to WebP (1280x720 max, quality 0.58) and limited to a Firestore-safe payload.
- Video uploads are limited to 12 MB before compression and compressed client-side to short 5-second max WebM, 480p max, ~360 kbps; final payload is capped before Firestore save.
- Every new image/video upload replaces the previous image, video data, and video URL.
- Showcase standalone renderer supports compressed image and compressed video media.
- Existing video URL support remains available as a fallback.
