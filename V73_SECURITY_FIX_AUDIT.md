# Dourak V73 — Authentication / Firestore Security Fix

## Purpose
V73 is a complete replacement build based on Dourak V72 Authentication Complete. It fixes the Firestore `users/{uid}` rules mismatch found in V72: the authentication profile writer stores `authProvider` and `emailVerified`, but V72's field allow-lists did not include them.

## Changes
- Added `authProvider` and `emailVerified` to the `users/{uid}` create allow-list.
- Added `authProvider` and `emailVerified` to the `users/{uid}` update affected-field allow-list.
- Added type validation when either field is present:
  - `authProvider` must be a string.
  - `emailVerified` must be a boolean.
- No broad `allow read, write` rule was introduced.
- Existing authentication/business/queue/display workflows were preserved.
- App cache-bust marker moved from `v=72` to `v=73`.

## Why this is needed
`ensureUserProfile()` writes:
- `email`
- `phone`
- `authProvider`
- `emailVerified`
- `updatedAt`

Firestore `hasOnly()` / `affectedKeys().hasOnly()` rules reject fields that are not explicitly allow-listed. Firebase documents this field-level allow-list pattern as a way to constrain client writes. See: https://firebase.google.com/docs/firestore/security/rules-fields

## Verification
- Inline JavaScript syntax: PASS
- Existing deep audit: PASS
- Existing smoke test: PASS
- Custom V73 rules/auth static audit: PASS
- ZIP integrity: PASS

## Known scope
Phone/SMS authentication remains optional and is not required for the free Spark setup. Google and Email/Password are supported by the V72 authentication layer.
