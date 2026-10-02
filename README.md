Dourak V54 — Complete Final Project

## V107 — security hardening (see SECURITY_AUDIT.md)
Full audit of the Firestore rules and client code. Fixed 3 critical issues (self-granted admin, self-granted staff membership, readable 4-digit staff passcodes), 4 high (OTP/approval bypass, counter tampering, public bookings, client-only capacity) and several medium/low ones. Added `qa/test_security_write_shapes.py` and a GitHub Actions check that runs the rules through Google's real emulator. **Deploy order matters — read SECURITY_AUDIT.md → "Deployment order" before publishing the rules.**

## V106 — app-wide theme system + "دوري" badge fix
**Theme:** measured every text element on 18 screens: 83 of 293 unreadable under كلاسيك+dark (and problems in every other combination). Replaced ~115 scattered dark-mode overrides with one token system — each theme/mode defines its palette once, every component reads it, and the legacy variables now point at the tokens. Result: 0 elements below WCAG 4.5:1 in all 4 combinations. **Badge:** the customer's ticket listeners depended on the places list, which wasn't loaded yet at start-up — so there was usually no listener at all and served tickets never left the (saved) local list. Listeners now follow the customer's own tickets. See QA_REPORT.md #37–38.

## V105 — owner header rebuilt as one design system (root fix for V103/V104)
V103/V104 were patches validated against an empty placeholder business, so they never rendered the business name, code card or hours — which stayed invisible. Root cause: every header element was hardcoded white for a dark header while one theme flipped only the background to light. Replaced ~9 scattered per-theme rules (and both earlier patches) with colour tokens on `.owner-head` that every child reads; themes set tokens only. "كلاسيك" now has a graphite header over a light page with a blue call-to-action. Measured with realistic content: all 11 header elements pass WCAG 4.5:1 in every theme / light-dark / button-state combination. See QA_REPORT.md #36.

## V104 — same theme, visual hierarchy fixed (header/cards/background all looked flat)
Follow-up per a second photo: the text-visibility fix (V103) was correct but the theme still looked "blended together" — three separate, redundant `--bg`/`--card` variable blocks accumulated across many past edits had left the header, its stat cards, the page background, and the cards below all within a few RGB points of each other. Added one final stylesheet giving each layer a real, distinct tone and adding actual shadows — confirmed via rendered-pixel measurement (not CSS values) that separation went from ~0 to ~11–27 points between layers, with the other theme re-confirmed pixel-identical to before. See QA_REPORT.md #35.

## V103 — invisible numbers under the "كلاسيك" theme, fixed
Confirmed by a real photo, pixel-matched with a live render: the theme labeled "كلاسيك" internally applies `theme-apple` CSS (the labels are swapped from the underlying preset names) — which switches the owner home header to a light background. Two elements never got a matching light-theme override for their hardcoded white text (`.owner-stat b`, `.walkin-btn`), unlike every sibling color on that same header — leaving the queue stat numbers and "عميل بالمحل" invisible. See QA_REPORT.md #34.

## V102 — standalone display link restricted to the owner only
Per explicit request: the `?display=<id>` link could be opened by any signed-in staff member, not just the owner — Firestore rules can't tell "staff in the normal app" apart from "staff opening this specific link" (both are identical reads), so the fix is an app-level check instead: the signed-in uid must match the business's `ownerId` or the page shows a clear "owner only" message. Staff's access to the normal in-app queue screen is unaffected. See QA_REPORT.md #33.

## V101 — QR scan (signed out) goes straight to email login with a direct instruction
Per explicit request: a signed-out customer scanning a QR no longer lands on the generic "عميل جديد"/"مكان جديد" landing choice — it skips straight to the actual email login/register form, with the subtitle replaced by a direct instruction that names the actual business once it loads. The existing automatic-join-after-registering chain (verified in V94) is unchanged; only what the customer sees first is different. See QA_REPORT.md #32.

## V100 — English voice completed ("Selene")
New recording makes English a real ready-made preset instead of the device-speech placeholder — all 3 dropdown languages (Egyptian, MSA, English) are now real, complete voices. Found and fixed a second real bug while integrating it: applying a preset looked up its clips by the recorder's *current* language tab rather than the preset's *own* language — English-only Selene, selected while the recorder defaulted to Arabic, silently wrote nothing at all with zero error shown. Now correctly resolves from the preset itself; different-language packs (Arabic + English) coexist independently, only same-language switches replace each other. See QA_REPORT.md #31.

## V99 — "الفصحى" voice completed, Khaleeji removed
New recording ("فاطمة") makes MSA a real ready-made preset instead of the device-speech placeholder; Khaleeji removed from the dropdown per request. Found and fixed a real bug while integrating it: switching between two voice presets left the previous one's uncovered clips (suffix/recall) behind, mixing two different voices' audio on the TV — a preset switch now cleanly replaces the whole voice. See QA_REPORT.md #30.

## V98 — call-voice dialect dropdown
Renamed the Egyptian voice from a person's name to "المصرية", and turned the single preset button into a dropdown: المصرية (ready), الخليجية (clearly marked as needing a recording — no TTS engine here to fake one), العربية الفصحى and English (both clear any custom pack and defer to the TV's own live device speech, which the engine already prefers anyway). See QA_REPORT.md #29.

## V97 — landing screen theme/language buttons visually matched
Confirmed by a real iPhone photo: the theme toggle and language pill had drifted apart in size, corner radius, and color over many past edits (conflicting !important rules). Fixed with a scoped rule for just these two elements — same height, radius, and treatment now — without touching the shared button classes used elsewhere in the app. See QA_REPORT.md #28.

## V96 — guest-mode account screen shows login, not logout
"حسابي" had a hardcoded logout button shown even in guest browsing mode, which has no real session behind it — an empty account placeholder next to a button with nothing to log out of, and no way back to a real account. Now shows "تسجيل الدخول" for guests, "تسجيل الخروج" only for an actual signed-in customer. Found and fixed a second real bug along the way: `setAttribute('onclick', ...)` with an inline `$('x')` call doesn't reliably see the script's own top-level `$` helper the way a static HTML attribute does — confirmed by an actual click-time error, not assumed. See QA_REPORT.md #27.

## V95 — logout now actually clears the customer's identity
Root cause of "after logout, logging back in as customer shows no real data": `logout()` never cleared `tbCustomerProfile` (name/governorate/phone), which has no per-account check anywhere it's read. The stale profile survived logout, so the next "عميل" entry found it and skipped registration entirely, landing on an empty-looking account screen with no real session behind it. Now clears every identity-bearing key on logout — the customer genuinely has to sign in again, every time. See QA_REPORT.md #26.

## V94 — QR-to-booking pipeline verified end-to-end
Audited per explicit request: each business's QR is unique by construction (Firestore document ID, not a guessable/collidable code). Confirmed working with real tests, not just code reading: logged-in customer scans → ticket created with zero taps; logged-out customer scans → shown auth → registers → first-time onboarding → auto-books immediately after, same zero-tap result, scan intent preserved across the whole chain. One nuance flagged for a product decision rather than changed silently: a multi-service business still asks which service (a one-tap picker) since the app can't guess intent — see QA_REPORT.md #25.

## V93 — role-confusion safety net + account-info card
Root cause found for reports of "confusion and bugs" in registration: `role` was set purely by which landing button was tapped and persisted unconditionally, with no check against the account's actual established role — a wrong tap could permanently misroute an owner into the customer experience (or vice versa) on that device. Now reconciled both directions without forcing either: a confirmation step before creating a new business when a customer profile already exists on the account, and a dismissible "open dashboard" banner when a customer session's account also owns a business. Also added: "حساب الدخول" card in Owner Settings, showing the actual signed-in email (live from Firebase Auth) + provider + a logout button — there was previously no way to confirm which account was signed in anywhere in the app.

## V92 — recovery from Google "origin_mismatch" dead-end
This is a Google Cloud Console configuration issue (the OAuth client's Authorized JavaScript origins), not a code bug — see the message to the user for the exact fix. Added a code-level safety net regardless: if Google's popup gets stuck with zero callback (exactly what origin_mismatch causes), a 10s timeout resets the button and automatically falls back to the Firebase flow instead of leaving a permanent dead end.

## V91 — voice preset finished (letter A + new phrase) + phone/TV sound fully decoupled
Added the missing letter "A" clip; replaced "دورك يا عمنا" with "دورك يا غالي" per the latest recording — all 14 slots now filled. Also: the Settings sound switch is relabeled "كتم صوت الهاتف" with an explicit note that it never affects the TV screen, and the TV audio engine no longer reads the phone's mute state at all (previously a shared variable — a latent coupling risk, now structurally impossible).

## V88 — Google sign-in on iPhone (configured)
Safari blocks the third-party storage Firebase's Google popup/redirect need. iPhone and the installed app now use Google Identity Services → signInWithCredential. Client ID is set: `379096322950-210cbqtb3rif9c475a3qmb9e95m6arq5.apps.googleusercontent.com`.

## V86 — login stays signed in, working password reset, iPhone start screen
Startup no longer replaces a real account with an anonymous one on every load (root cause of repeated logins / iPhone not entering / multi-tap Google). Reset email retries without a rejected continue URL; email-only reset mode; phone login hidden; iOS alignment fixes. See QA_REPORT.md #14–17.

## V85 — cancellation-abuse protection
Confirm-before-cancel with escalating warnings; max 3 customer cancellations per place per 24h, enforced in Firestore rules (`customerStats`). See QA_REPORT.md #13.

## V84 — secure OTP + private customer contacts
OTP is generated by the owner into owner-only `otpSecrets` and verified by Firestore rules (max 5 attempts). Customer names/phones moved from public tickets to owner-only `ticketContacts`; legacy tickets auto-migrate. See QA_REPORT.md #11–12.

## V83 — full QA pass
See `QA_REPORT.md` (10 bugs fixed incl. 1 critical rules leak; open findings with recommendations) and `qa/` (re-runnable suites).

## V82 — "Install Dourak" button + pop-up blocking fixes

**Install button** on the start screen (hidden once the app is installed).
Android/Chrome: the real one-tap install prompt (`beforeinstallprompt` is
captured whenever offered). iPhone (no install API exists): clear Safari
"Add to Home Screen" steps. In-app browsers (WhatsApp/Instagram/Facebook)
can't install at all: told to open in Chrome/Safari, with a copy-link button.
Root cause of the icon not being offered automatically: there was **no
service worker** (and the build migration unregistered any). Added `sw.js`
that caches nothing — every request still hits the network, so deploys show
instantly — and only serves a small offline page for failed navigations.
The build migration now keeps `sw.js`. Manifest gained `id`/`scope`; iOS
home-screen meta tags added.

**Pop-up blocking.** Browsers allow `window.open()` only directly inside a
tap. `sendTokenWhatsapp` awaited two Firestore reads first, so it was
*always* blocked; `openBusinessMap` was blocked whenever the place wasn't
cached; `openDisplayWindow` dead-ended with a toast. New central helper:
open synchronously from on-screen data when possible; otherwise reserve a
tab inside the tap and point it after the read; and if a browser still
refuses, show a sheet with a real link (a tapped `<a target=_blank>` is
never a pop-up). Firestore rules unchanged.

Verified in headless Chromium with emulated iPhone / Android / WhatsApp
in-app user agents, a simulated Android install prompt, and blocked
`window.open`. Real-device install still needs a check on an actual phone.


## In-app call-voice recorder (V81) — spoken calls on TVs with no speech engine

The TV correctly fell back to chime-only because its browser has no
`speechSynthesis`. The voice-pack layer is the fix, but manual files +
manifest + GitHub upload is not a realistic owner workflow. New:
**Queue display → 🎙️ تسجيل صوت النداء للتلفزيون** in the owner app.

- The owner records each word separately on their phone ("الرقم", 0–9,
  "تفضل إلى الخدمة"; optional "A" and "نداء مرة أخرى").
- Each clip is processed on the phone: silence trimmed both ends, volume
  normalized, short fades, converted to 16 kHz mono 16-bit WAV (~20 KB) —
  a format virtually every TV can decode (phone-native WebM/AAC is not).
- Saved to `businesses/{id}/voicePack/{lang}_{key}`; the business gets a
  `voicePackUpdatedAt` stamp so a running TV drops its cached voice via the
  business listener it already has (no new listener) and uses the new
  recording on the next call — no TV refresh needed.
- The TV engine now prefers a recorded pack over everything else (same
  voice on every TV, no speech engine needed), then speechSynthesis, then
  online TTS, then chime-only. Static `voice/` files still work as before.
- Fixed: the engine could create a second AudioContext when one already
  existed on the page; it now always reuses the shared one.

**Firestore rules changed (must be published):** new `voicePack`
subcollection (read: signed-in, i.e. the display; write: owner/admin only,
`lang` in ar/en, `dataUrl` < 350 KB) and `voicePackUpdatedAt` added to the
business update allowlist.

**Verified end-to-end in headless Chromium:** fake microphone → recorder →
processed WAV (RIFF/WAVE, mono, 16 kHz, 16-bit) → mocked Firestore → TV with
speechSynthesis removed → 4 recorded clips played for "الرقم A 1 2";
dedupe/recall/newest-wins/stub/no-speech regressions pass; zero page errors.
Not verified here: a real phone microphone and a real Smart TV.


## TV Audio Engine (DourakTVAudio) — the real cause of "unsupported"

**Root cause.** `unsupported` means the TV browser has no `speechSynthesis`
at all (common on Samsung Tizen, LG webOS, most Android TV WebViews). Many
others expose the API as a silent stub. Every earlier fix assumed speech
existed. Two further bugs: recall never reached the TV (nothing was written
to Firestore), and a refresh re-announced the customer already being served.

**Architecture.** One isolated engine, `window.DourakTVAudio`
(`init/unlock/resume/playChime/speak/announce/stop/isUnlocked/isSupported`),
shared by all 7 layouts. Per announcement: visual flash → Web Audio chime
(one reused AudioContext; recreated only if `closed`) → `speechSynthesis`
(voice loader + `voiceschanged` + retry; stub detected via "no onstart in
2.5s") → offline voice pack from `voice/<lang>/` played on the same
AudioContext → online TTS via one reusable `<audio>` element unlocked
during the tap → otherwise chime + flash only, with an honest status.
Newest call cancels any announcement in progress (no pile-up). Old
function names remain as thin wrappers.

**Duplicate prevention.** Key = ticket id + `recalledAt`. The first
*server* snapshot only sets the baseline (refresh/reconnect never
re-announce). `recallCustomer()` now stamps `recalledAt` so the TV
announces recalls. The old 20s silent-utterance keep-alive was removed
(likely source of the earlier `interrupted` error); recovery now only
resumes an already-unlocked context on visibility/focus/pageshow/
fullscreen and every 25s.

**Firestore rules: not changed** (owner/staff already may update tickets).
No new Firebase listeners (display still has exactly 3).

**Verified here (code-level, headless Chromium):** syntax, structure,
handlers, listener count; dedupe; recall; newest-wins; no-speech TV path;
stub-engine detection; zero page errors. **Not verifiable here:** a real
Smart TV, the strict-autoplay "locked" path, and online TTS (no network in
this sandbox; it is an unofficial best-effort endpoint). The offline voice
pack (`voice/README.md`) is the reliable path for speech-less TVs.

## TV announcement keep-alive, last-served-number persistence, and a new last-call-time cutoff

**TV display voice announcement on "استدعاء التالي".** The
infrastructure for this was already fully built and correctly wired —
the display page's realtime listener already detects a new call and
triggers the announcement. The most likely real-world reason it doesn't
reliably play: a TV left running for hours with zero direct interaction
is exactly the scenario browsers' autoplay/audio-suspension policies
target (Chrome in particular has a well-documented bug where
`AudioContext` gets suspended and `speechSynthesis` effectively stalls
after a period of silence, even after the initial gesture-unlock). Added
a quiet 20-second keep-alive that resumes both and speaks a near-silent
utterance to keep the speech queue from going idle-stale, so whenever
the real announcement arrives — possibly hours after the page loaded —
it's speaking to an engine that's already warm rather than one that has
to wake up first.

**The display no longer resets to 0 after the last customer is
served.** `callNext()` was explicitly setting `currentNumber = 0`
whenever a customer was served with no one else waiting — now it stays
on that customer's own number, which reads as "here's who we just
finished with" instead of looking like an error/empty state. Fixed in
both the Firestore transaction and the matching local state update.

**New: "آخر موعد لأخذ توكن" (last time to take a token)**, in "قائمة
الانتظار" — a cutoff separate from the business's actual closing time.
Once set, both a customer booking online and the owner adding an
in-store walk-in are blocked from creating a *new* token past that
time, with a clear, distinct message from "closed" — while everyone
already in the queue keeps being served normally right up to actual
closing. The indicator turns the same red/warning color already used
for "at capacity" once the cutoff has passed for the day, and the time
comparison is normalized relative to the business's own opening time
(not a raw clock comparison), so it stays correct even for a business
whose hours cross midnight.

All fixes re-verified: div/section/style balance intact, JS syntax
valid, zero onclick handlers pointing at undefined functions, live
render confirmed clean.

## TV display "interrupted" speech error — the diagnostic fix paid off

The last round's diagnostic improvement worked exactly as intended —
this time the actual error code came back: `"interrupted"`. That
specific code from the Web Speech API almost always means a *newer*
`speak()` call cut off an earlier one still in progress — commonly
caused by a duplicate button press, and TV remotes are notorious for
double-firing a slow "OK" button. Two fixes:

- `speakDisplayHuman()` now treats `"interrupted"`/`"canceled"`
  specifically as benign (a newer attempt took over) rather than a real
  failure — it no longer shows an alarming "تعذر تشغيل الصوت" message
  for something that isn't actually a problem.
- Added an in-flight guard so a second, near-simultaneous tap on
  "تفعيل الصوت" is simply ignored while the first attempt is still
  playing, rather than starting a second speech that would cut the
  first one off before it could even report success — fixing this at
  the source instead of only softening its symptom.

All fixes re-verified: div/section/style balance intact, JS syntax
valid, zero onclick handlers pointing at undefined functions.

## Google sign-in needing two taps — same root cause as the email-login and TV-speech gesture bugs

`signInWithPopup`/`linkWithPopup` use `window.open()` internally, which
many browsers require to be called synchronously within the click
handler that triggered it — but `loginGoogle()` started with
`await window.waitForDourakFirebase(10000)` before ever reaching the
popup call. Any `await`, even one resolving almost instantly, is enough
for the browser to stop treating what follows as directly
user-initiated, so the popup got silently blocked on the first tap.
By the second tap, `window.dourakFB.ready` was already `true` from the
first attempt, so the await resolved in the same tick and the popup
went through — which is exactly the "press once, nothing happens;
press again, it works" pattern being reported.

Fixed by checking readiness synchronously first: when Firebase is
already ready (the overwhelmingly common case, since it usually
finishes initializing well before someone reaches the login screen),
the popup call now happens with nothing awaited in front of it at all.
Only on the rare case where it genuinely isn't ready yet does it await
first — and in that case it deliberately switches to the redirect-based
sign-in flow instead of still attempting a popup, since a popup can no
longer be relied on to work after any await regardless.

All fixes re-verified: div/section/style balance intact, JS syntax
valid, zero onclick handlers pointing at undefined functions, live
render confirmed clean.

## Call-next button bug fixed, and deeper speech diagnostics

**Found the actual bug behind "pressing next on the last customer
doesn't work"**: `callNext()` itself was already correct — it was
`updateHomeServeButton()`'s button-disabling logic that was wrong. It
disabled `.callnext-btn` whenever `waitingCount === 0`, with no
exception for a customer who was still currently called. Since
completing the very last customer (nobody else waiting) is exactly what
pressing "استدعاء التالي" does in that situation, the button was being
disabled at precisely the moment it was needed. Fixed: it's now only
treated as "nothing to do" when there's *neither* a called customer
*nor* anyone waiting.

**Speech synthesis on the TV display — deeper diagnostics, since the
previous synchronous-call fix wasn't sufficient on its own.** Two more
things fixed: the real error code from the Web Speech API (`not-allowed`,
`network`, `synthesis-failed`, etc.) was being discarded entirely and
replaced with a generic "not supported" message — it's now captured and
shown directly, so the next report will say exactly what's actually
failing instead of a guess. Also removed `speechSynthesis.cancel()`
immediately before the very first `speak()` call — on some engines,
calling cancel and speak synchronously in the same tick spuriously
cancels the utterance that was just queued, and there was nothing
legitimate to cancel yet on a first "enable audio" tap anyway.

All fixes re-verified: div/section/style balance intact, JS syntax
valid, zero onclick handlers pointing at undefined functions.

## The actual root cause of the green-area bug, found and fixed definitively

Every previous attempt at this (`overscroll-behavior`, the bfcache
`pageshow` reset, `background-attachment: fixed`) was fixing a real but
secondary issue — none of them were the actual cause, confirmed with a
live test: `document.getElementById('publicDisplay')` was rendering
with `display: flex` and a full `100vh` height on every single page
load, `hidden` class or not.

The real cause: `.display-page{display:flex!important}` (part of the
accumulated display-styling overrides) and `.hidden{display:none!
important}` are both single-class selectors with equal specificity —
when two `!important` declarations tie on specificity, CSS falls back
to source order, and `.display-page` sits later in the stylesheet. It
was winning every time, completely defeating `.hidden` on
`#publicDisplay` regardless of whether the class was correctly applied
(it always was). This meant the display page's own background and
controls — including its sound-toggle button — sat there, fully
visible, at full viewport height, on literally every screen in the
app, right below whatever content was actually showing, extending the
page's scrollable height by a full extra screen's worth every time.

Fixed with `#publicDisplay.hidden{display:none!important}` — an
ID+class selector has higher specificity than a plain class selector
even when both use `!important`, so this wins unconditionally
regardless of where anything else sits in the file, closing this off
for good rather than depending on managing source order in an already
very large, accumulated stylesheet.

**Verified with a live test, not just visual inspection**: before the
fix, `getComputedStyle(publicDisplay).display` was `"flex"` and
`body.scrollHeight` was double the viewport height. After the fix,
`display` is `"none"`, height is `0`, and `body.scrollHeight` exactly
equals the viewport — there is no longer any extra scrollable area at
all.

## Follow-up round: display-leak bfcache bug, TV speech gesture bug, and login feedback

**Found the real cause of the green area + display sound option
leaking into regular screens.** It wasn't the overscroll fix from the
previous round being insufficient — it was a separate bug entirely. The
`pageshow` bfcache-restore handler only ever handled the owner/staff
role, and never reset `#publicDisplay`'s hidden state or the
`display-mode`/`display-immersive-mode` classes on `html`/`body`. If
the browser restored this SPA from its back-forward cache after any
visit to a `?display=` link, `boot()` never re-ran (that's how bfcache
restores work), so nothing ever re-hid the display page's elements —
including its sound-toggle button — leaving them sitting, visible,
underneath the normal screen. Now resets all of that defensively on
every persisted restore, for every role, not just owner/staff.

**Found the real cause of "الصوت غير مدعوم" on the TV display,
consistent across every browser tried.** It was never actually a
browser-support problem — `speechSynthesis.speak()` was being called
inside a `setTimeout`, even a short 120ms one, which is enough for most
browsers' autoplay/gesture policy to stop treating it as directly
user-initiated and silently refuse it. Now speaks immediately,
synchronously, within the same click handler that triggered it — the
short delayed retry still exists, but only as a fallback for the
separate, genuine issue of some TV browsers populating their voice list
lazily, not as the only attempt.

**Email login could take several tries and feel unresponsive.** The
button only went silently `disabled` with no visual change while
waiting on Firebase (`waitForDourakFirebase` can legitimately take up
to 10s on a slow connection) — indistinguishable from the tap having
done nothing at all, which is exactly what was leading to repeated
taps. Now shows "...جاري التحقق" clearly the whole time, always
restored to its real label afterward regardless of outcome.

All fixes re-verified: div/section/style balance intact, JS syntax
valid, live tests confirm the loading state renders correctly.

## Scroll/overscroll fix + performance and responsiveness pass

**Fixed the green area appearing when scrolling to the bottom.** The
page body has an intentional subtle green-tinted gradient (part of the
theme, meant to frame the white card around its edges) — with no
`overscroll-behavior` set, scrolling past the bottom (rubber-band
bounce, common on iOS and some Android browsers) revealed more of that
background than intended, looking like a bug rather than the
edge-of-page effect it actually was. Added `overscroll-behavior-y: none`
on `html`/`body` so the page can no longer bounce past its own content.

**Speed/responsiveness pass:**
- Added `touch-action: manipulation` globally and directly on
  interactive elements — removes the ~300ms tap-response delay mobile
  browsers otherwise add while waiting to rule out a double-tap zoom
  gesture. Every tap now registers essentially instantly.
- Buttons now get an immediate `:active` press-down (scale .97) so a
  tap feels acknowledged right away, before whatever network request it
  triggered has even started — and the button's own hover/press
  transition sped up (180ms → 120ms).
- The bottom sheet/modal previously popped into view instantly with no
  transition at all (`display:none` → `display:flex` isn't animatable).
  Added a fast (180ms) slide-up + fade-in so it now feels intentional
  and smooth rather than abrupt, without feeling slow.
- Removed an unnecessary 700ms artificial delay between the app
  finishing boot and the splash screen starting to hide (now 250ms) —
  faster perceived startup with no functional change.

All fixes re-verified: div/section/style balance intact, JS syntax
valid, live render confirmed clean.

## V79 round — re-applied prior fixes + new boot race condition fixed

This V79 upload branched from an earlier, unfixed baseline, so the five
fixes from the previous review round were re-applied (same bugs, same
locations, confirmed identical before fixing):
- Two unmatched extra `</div>` tags (`oHome` closing `owner-content`
  prematurely before the logout button; a stray extra one before
  `oSettings`'s closing `</section>`).
- Three `<style>` blocks with no closing `</style>` tag at all
  (`v47-auth-css`, `v52-fit-all-screens`, `v56-display-fit`).
- `requireCustomerRegistration()` now requires `isPermanentAuthUser()`,
  not just explicit guest mode.
- `logout()` now actually calls `auth.signOut()` (awaited before the
  reload).
- The phone-auth box (fully built, `startPhoneAuth`/`verifyPhoneAuth`,
  reCAPTCHA) now has an actual toggle button revealing it — previously
  permanently hidden with no way to open it.

**New bug found and fixed — the reported "customer enters but places
never load and no registration prompt appears".** `boot()` read
`auth.currentUser` synchronously, before Firebase's first
`onAuthStateChanged` callback had actually fired (that's what sets
`window.dourakFB.ready`). Reading it that early returns
`null`/`undefined` regardless of whether a session — anonymous or
permanent — actually exists, since Firebase resolves this
asynchronously. This is a genuine race condition: whether it manifested
depended purely on how fast that resolution happened to complete
relative to when `boot()` happened to run, which is exactly the kind of
symptom that shows up intermittently rather than every single time.
Fixed by checking the already-set `window.dourakFB.ready` flag (already
resolved by `handleGoogleRedirectResult()`'s own internal wait just
above in the same function) and only adding a short additional wait if
it genuinely isn't ready yet — deliberately not a second full-length
wait stacked on top of the existing one, which would have doubled the
worst-case delay on a slow or broken connection for no benefit on the
normal, fast-connecting case.

All fixes re-verified together: div/section/style balance intact
(693/693, 27/27, 23/23), JS syntax valid, zero onclick handlers pointing
at undefined functions, and a live boot-sequence test confirms the app
correctly reaches a usable screen instead of hanging, both when
Firebase resolves normally and in the worst-case timeout path.

# Dourak V52 — Complete Final Package

دورك (Dourak) — نظام إدارة الدور والمواعيد.

## Included
- Customer / owner / staff flows
- Firebase / Firestore configuration and rules
- Cloud Functions under `functions/`
- Automated checks under `tests/`
- PWA assets and manifest
- V50 overnight-hours/display functionality
- V51 TV audio + human voice + promotion attention
- V52 Fit-to-All-Screens display mode

## Run checks
```bash
npm test
node tests/v52_feature_audit.js
```

## Important
This package is a source/project bundle. Live Firebase deployment and real-device TV/browser testing still require the project's Firebase credentials/environment and physical devices.

## V53 Display Pro Update
The independent TV/Tablet queue display now includes a side settings rail with manual size control (85%–118%), reset, and six professional themes. The owner dashboard can choose the business default theme. Promotion lock now disables and clears the live promotion so the banner stops on connected displays.

## V108 security release

See `RELEASE_GATE.md` and `APP_CHECK_PRODUCTION_SETUP.md` before production deployment. Staff authentication now requires Firebase App Check and server-side verification.
