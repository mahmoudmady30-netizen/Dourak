# Dourak V65 — Queue Workflow + Standalone Display Fit Audit

## Queue workflow
- `استدعاء التالي` now completes the currently `called` customer automatically before calling the next eligible waiting customer.
- The completion + next-call state changes are committed in one Firestore transaction.
- If there are no waiting customers, the `استدعاء التالي` button is disabled with a clear disabled style.
- The owner queue list remains realtime through `queueTickets` `onSnapshot` and is explicitly refreshed after each successful call workflow.
- Served counters, current number, waiting count, notifications, chime and speech remain synchronized.

## Showcase cleanup
- Removed placeholder advertisement phrases: `قهوة أفضل`, `Better Coffee`, `Brighter Days`, `يوم أجمل`.
- Removed the Showcase `التالي / Next` label; only the upcoming token cards remain.
- Empty Showcase media area is intentionally text-free.

## Near Turn
- Reworked into a balanced two-panel professional layout with current token, people-ahead stat, estimated-time stat and a clear stay-near panel.
- Responsive mobile layout collapses cleanly to one column.

## Standalone display controls
- Every standalone queue layout now renders the same Fill Screen control beside the DOURAK brand in the display header.
- The control is consistent across all seven layouts and updates its active state on `fullscreenchange`.
- Removed the old bottom-bar duplicate Fill Screen control.

## Promotions / messages fit
- Standalone display shell keeps the layout host flexible and reserves space for promotions/messages and system controls.
- Fixed/banner promotion text wraps to a maximum of two lines instead of being clipped at the bottom.
- Promotion sizing is constrained responsively so all seven layouts continue to fit the available viewport.

## Verification
- All inline JavaScript blocks: PASS
- `tests/deep_audit.js`: PASS
- `tests/smoke.js`: PASS
- Custom runtime renderer check for all 7 layouts: PASS
- Showcase stale-phrase scan: PASS
- Fill Screen control presence across all 7 layouts: PASS
- Firestore rules structural audit: PASS
