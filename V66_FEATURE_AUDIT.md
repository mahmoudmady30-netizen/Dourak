# Dourak V66 Feature Audit

Base: Dourak V65 Queue Workflow + Display Fit.

Changes:
- Renamed owner walk-in action from `+ عميل موجود` to `عميل بالمحل` in Arabic and `In-store customer` in English.
- Removed the plus sign from the action label.
- Walk-in name and phone fields are explicitly optional.
- If both walk-in fields are empty, the ticket is created as `عميل بالمحل` / `In-store customer` without changing existing queue/open/Firestore workflow conditions.
- Existing phone lookup remains active when a phone number is entered.
- `تم إنهاء الخدمة` is hidden whenever there are zero waiting customers, while Recall remains available for the currently called customer.
- When at least one waiting customer exists, the completion action becomes visible again.
- Existing `استدعاء التالي` disabled behavior when waitingCount is zero is preserved.

Verification:
- Inline JavaScript syntax: PASS (non-empty inline script blocks).
- `tests/deep_audit.js`: PASS.
- `tests/smoke.js`: PASS.
- `test_v65.js` queue display renderer checks: PASS for all 7 layouts.
- ZIP integrity: PASS.
