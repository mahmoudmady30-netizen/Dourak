# Dourak V68 Feature Audit

## Requested change
After a customer signs in and takes a queue turn, show the live number of remaining waiting customers at each active business with a small professional circular indicator.

## Implementation
- Added a dedicated realtime listener for `businesses/{businessId}/queue/current` for every business represented by the customer's active queue tickets.
- Uses Firestore `waitingCount` as the authoritative live source.
- Supports multiple active businesses at the same time.
- Cleans up stale business listeners when an active ticket disappears and when realtime is restarted.
- Queue cards now show a small circular live indicator with the remaining waiting count and a live pulse dot.
- The indicator is responsive and has a dedicated dark-mode treatment.
- Business cards for active customer businesses also receive the same live count in their underlying `count` field, so the displayed waiting count stays synchronized.
- No changes to queue issuance, cancellation, owner call-next workflow, Firestore rules, or existing display/immersive behavior.

## Verification
- 5 inline JavaScript blocks: syntax PASS.
- `tests/deep_audit.js`: PASS.
- `tests/smoke.js`: PASS.
- Firestore rules structural audit: PASS.
- Custom static checks for live queue listener, circular UI, multiple-business subscription, and cleanup: PASS.
- ZIP integrity: PASS.

## Runtime note
A real browser/TV session is not available in this environment, so realtime Firestore behavior is verified structurally and through the existing application wiring, not by a live external Firebase session.
