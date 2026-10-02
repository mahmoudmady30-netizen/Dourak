# Dourak V62 — Queue Control & Owner Persistence Audit

## Requested fixes

1. Removed the duplicate **شاشة الطابور** entry from the owner **الأداء والمتابعة** category. The display remains only in the primary daily-operations category and its dedicated screen.
2. Reworked the owner **استدعاء التالي** control so it is not disabled by a stale local queue array. The handler reads the authoritative Firestore queue, prevents double-click races, and gives explicit feedback when the queue is empty or a current customer is still called.
3. Walk-in customers are created as real `queueTickets` records and the owner queue list is updated optimistically immediately after the transaction, then reconciled by the realtime listener.
4. Owner-side realtime no longer treats owner-created walk-ins as if the owner were a customer on the customer queue listener.
5. Owner business persistence is now defensive:
   - Firebase anonymous auth persistence is explicitly set to LOCAL.
   - The active Firebase UID is cached only as an identity marker.
   - A missing owner query no longer clears the active place immediately.
   - The cached business document is revalidated directly by `ownerId == current Firebase UID`.
   - `accountId == current Firebase UID` is a secondary recovery path, still requiring `ownerId == current Firebase UID`.
   - A transient read/query problem cannot turn into "register your place again".
   - A business cached under a different authenticated UID is never reused.

## Verification

- All inline JavaScript blocks: PASS (`node --check`).
- Deep audit: PASS.
- Smoke tests: PASS.
- No duplicate named function declarations: PASS.
- Inline UI handlers: PASS.
- Firestore rules structural audit: PASS.
- Owner home contains one Queue Display entry in the daily-operations category; the duplicate performance-category entry is removed.
- Queue Display owner page contains compact layout links with Open/Copy actions; no full-screen layout gallery is rendered.
- Standalone display fixes from V61 are preserved.

## Runtime limitation

A real Firebase browser session against the production project was not executed in this container. The call flow and persistence fixes were therefore validated by source-level analysis, JavaScript parsing, existing deep/smoke audits, and targeted static checks. No claim of a manual TV/device session is made.
