# Dourak — Security Audit (V107)

Date: 2026-09-26. Scope: `firestore.rules` (the app's only server-side
security boundary — there is no backend) and `index.html` (all client code).

## Summary

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | 🔴 Critical | Any signed-in account could make itself platform admin: the admin link had no code, and the rules let every user write `role: 'admin'` on their own user doc, which `isAdmin()` trusted. | Fixed |
| 2 | 🔴 Critical | Any account could make itself staff of any business without a passcode: the app wrote `users/{uid}.staffOf` itself and `isStaffOf()` trusted it. Staff access exposes customer names/phones, OTP codes and queue control. | Fixed |
| 3 | 🔴 Critical | Staff passcodes were readable by any signed-in account (on the public staff record and in `staffLogins`), were only 4 digits, and came from `Math.random`. | Fixed |
| 4 | 🟠 High | The owner's "OTP" and "approval" confirmation modes were enforced only on the device; a modified client could create a ticket directly as `waiting`. | Fixed |
| 5 | 🟠 High | Queue counters (`waitingCount`, `nextNumber`, appointment counter) could be moved by any signed-in account without a ticket — e.g. to make a queue look full. | Fixed |
| 6 | 🟠 High | Every booking (who booked where and when) was readable by every signed-in account. | Fixed |
| 7 | 🟠 High | `maxQueueCapacity` was enforced only on the device. | Fixed |
| 8 | 🟡 Medium | Any owner could set their business code to another business's code and capture its code searches. | Fixed |
| 9 | 🟡 Medium | A customer could post a chat message labelled as sent by the owner. | Fixed |
| 10 | 🟡 Medium | Notifications, reviews, messages and contact fields had no length limits. | Fixed |
| 11 | 🟡 Medium | Tickets could reference services that don't exist or are inactive. | Fixed |
| 12 | 🔵 Low | External-link opener accepted any URL scheme (no exploitable caller found). | Fixed (allowlist) |
| 13 | 🔵 Low | No click-jacking guard / baseline content policy. | Fixed (frame guard, `object-src 'none'; base-uri 'self'`) |
| — | ✅ | Cross-site scripting: every user-controlled text field was rendered on every customer, owner, display and preview screen; no injected code executed. | No issue |

## How each fix works

1. **Admin** — `isAdmin()` now requires a document `admins/{uid}` that no
   client can write; it is created only in the Firebase Console. `users.role`
   can only be `customer`. The admin screen shows the account ID to add.
2. **Staff membership** — `isStaffOf()` now requires
   `businesses/{id}/staffSessions/{uid}`, which the rules accept only after
   verifying the passcode (below). Deleting a staff member deletes their
   passcode and ends their sessions.
3. **Staff passcodes** — stored only in `businesses/{id}/staffSecrets/{staffId}`
   (owner-readable only). New passcodes are 6 digits from the browser's
   cryptographic generator. Login is a two-step: a counted attempt in
   `staffAuth/{staffId}` (max 8 per 15 minutes per staff member), then a
   session the rules accept only if that attempt matches the stored
   passcode. Existing passcodes are moved automatically the first time the
   owner opens the staff screen; the owner is advised to change them because
   they were exposed before this update.
4. **Confirmation mode** — the rules compute the required starting status
   from the business's `confirmationMode`; owner/staff walk-ins are exempt.
5. **Counters** — every customer counter change must name the ticket written
   in the same transaction (`lastIssuedTicketId`, `lastCancelledTicketId`,
   `lastActivatedTicketId`), and that ticket must belong to the caller and
   actually be created / cancelled / activated in that transaction.
6. **Bookings** — readable only by the customer and the business it belongs to.
7. **Capacity** — checked by the rules on every customer join.
8. **Business codes** — `businessCodes/{code}` is created once and must point
   back at the business carrying the code; a code can't be changed once set.
   Search uses this registry and refuses ambiguous old-style duplicates.
9–11. Sender role must match the sender; string length caps; service must
   exist and be active.

## Verification

- **Client write shapes** (`qa/test_security_write_shapes.py`, 21 checks):
  records every write the app makes in staff creation, legacy-passcode
  migration, staff login, queue join and admin login, and checks each matches
  what the new rules require. All pass.
- **Full regression suite**: all existing suites pass (unit, responsive smoke,
  contrast, auth, QR, OTP/PII, cancellation limits, voice, TV audio…).
- **Rules against Google's real engine** (`qa/rules/rules.test.mjs`, 26
  tests): **not run in this sandbox** — the Firestore emulator download is
  blocked by the sandbox's network policy. They run automatically in GitHub
  Actions (`.github/workflows/firestore-rules.yml`) on every push that
  touches the rules. **Publish the rules only after that check is green.**

## Deployment order (important)

1. Push the code to GitHub first (the app must send the new fields before the
   new rules require them).
2. Wait for the "Firestore rules" check on the commit to turn green.
3. Firebase Console → Firestore → Rules → paste `firestore.rules` → Publish.
4. To keep your own admin access: open the admin screen once, copy the
   account ID shown, then Firebase Console → Firestore → create collection
   `admins` → document with that ID (any field, e.g. `note: "me"`).
5. Open the owner app → staff screen once per business (moves old passcodes),
   then change each staff passcode.

## What still needs the Firebase Console (can't be done from code)

- **App Check** (reCAPTCHA) — the strongest remaining protection against
  scripted abuse (mass fake bookings from many throw-away accounts). Rules
  can't rate-limit across accounts.
- **API key restrictions** — HTTP referrers + only the Firebase APIs used.
- **Authorized domains** — only your real domains.

## Honest limits

No system is "impossible to hack". These fixes close every hole found in this
audit and move all trust decisions to the server-side rules, but they don't
replace App Check, periodic re-audits, and keeping Firebase access (Console
login, GitHub account) protected with 2-step verification — an attacker with
your Google or GitHub password bypasses every rule above.
