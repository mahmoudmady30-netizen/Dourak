# DOURAK V69 — QR Auto-Join Fix Audit

## Requested behavior
- The owner's business QR must open the specific business, not just the generic app home.
- A fresh/unauthenticated customer who scans the QR is sent through the existing customer registration flow.
- An existing customer is sent through the existing login flow.
- After authentication/onboarding, the original QR business is restored automatically and the existing `joinQueue()` workflow is resumed.
- The QR target is persisted during authentication so slow Firebase boot or the onboarding screen cannot lose the business context.
- The QR URL is distinct from the normal public business URL: `?business=<id>&join=1`.
- Existing public/preview links remain unchanged.

## Implementation
- `captureQrJoinFromUrl()` captures the QR target before authentication and stores it in localStorage.
- `applyPublicBusinessFromUrl()` consumes the pending QR target after customer session resolution and calls `choosePlace(businessId, true)`.
- `openQr()` now generates the QR from `getBusinessJoinUrl()`.
- Existing `requireCustomerRegistration()` remains the gate before a real queue ticket is created.
- Existing customer registration/login/onboarding callbacks remain intact.
- For a business with exactly one active service, QR auto-joins that service immediately after authentication. Businesses with multiple services still show the normal service picker so the customer can choose the correct service rather than silently selecting the wrong one.

## Verification
- `node tests/deep_audit.js`: PASS
- `node tests/smoke.js`: PASS
- All 5 inline JavaScript blocks: PASS syntax check
- QR join URL/capture/resume static checks: PASS
- Firestore rules structural audit: PASS via deep audit
- ZIP integrity: to be verified after packaging
