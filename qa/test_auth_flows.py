import pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent; APP_URL = ROOT.parent.joinpath('index.html').as_uri(); res = []
def check(name, ok, detail=''): res.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))
# Fake Firebase Auth mirroring the real behaviour that matters here:
# signInAnonymously() REPLACES a signed-in real (non-anonymous) account.
FAKE = r"""
(() => { const S = window.__auth = { anonCalls: 0, resetCalls: [], user: window.__INITIAL_USER || null, cbs: [] };
  const notify = () => S.cbs.slice().forEach((cb) => cb(S.user));
  const auth = { get currentUser() { return S.user; },
    onAuthStateChanged(cb) { S.cbs.push(cb); setTimeout(() => cb(S.user), 60); return () => { S.cbs = S.cbs.filter((c) => c !== cb); }; },
    setPersistence: () => Promise.resolve(),
    signInAnonymously: async () => { S.anonCalls++; if (!S.user || !S.user.isAnonymous) S.user = { uid: 'anon' + S.anonCalls, isAnonymous: true, providerData: [] }; notify(); return { user: S.user }; },
    getRedirectResult: async () => ({ user: null }),
    sendPasswordResetEmail: async (email, settings) => { S.resetCalls.push(settings ? 'with-continue-url' : 'plain'); if (settings) { const e = new Error('continue uri'); e.code = 'auth/unauthorized-continue-uri'; throw e; } },
    signOut: async () => { S.user = null; notify(); } };
  const doc = () => ({ set: async () => {}, get: async () => ({ exists: false, data: () => ({}) }), update: async () => {}, collection: () => col() });
  const col = () => ({ doc, where: () => col(), orderBy: () => col(), limit: () => col(), get: async () => ({ docs: [], empty: true }), onSnapshot: () => () => {} });
  const fs = () => ({ collection: col, runTransaction: async (f) => f({ get: async () => ({ exists: false, data: () => ({}) }), set() {}, update() {} }) });
  fs.FieldValue = { serverTimestamp: () => ({}), delete: () => ({}) };
  const a = () => auth; a.Auth = { Persistence: { LOCAL: 'local' } }; a.GoogleAuthProvider = function () { this.setCustomParameters = () => {}; }; a.EmailAuthProvider = { credential: () => ({}) };
  window.firebase = { initializeApp: () => ({}), auth: a, firestore: fs, apps: [] };
  Object.defineProperty(window, 'firebase', { value: window.firebase, writable: false });
})();
"""
def run(name, init_user=None, pending_redirect=False):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:80]))
        pre = f"window.__INITIAL_USER = {init_user or 'null'};" + ("sessionStorage.setItem('dourakGoogleRedirectMode','signin');" if pending_redirect else "")
        pg.add_init_script(pre + FAKE); pg.goto(APP_URL); pg.wait_for_timeout(1500)
        out = pg.evaluate("({anonCalls: __auth.anonCalls, user: __auth.user && {uid: __auth.user.uid, anon: __auth.user.isAnonymous}})")
        b.close(); return out, errs
o, e = run('real account restored', "{uid:'realUser1',isAnonymous:false,email:'m@x.com',providerData:[{providerId:'password'}]}")
check('saved real account survives a reload (NOT replaced by anonymous)', o['user'] and o['user']['uid'] == 'realUser1' and o['anonCalls'] == 0, str(o))
o, e = run('anonymous restored', "{uid:'anonOld',isAnonymous:true,providerData:[]}")
check('saved anonymous session is reused (no new anonymous user)', o['anonCalls'] == 0 and o['user']['uid'] == 'anonOld', str(o))
o, e = run('first visit')
check('first visit gets an anonymous session so places can load', o['anonCalls'] == 1 and o['user']['anon'], str(o))
o, e = run('google redirect pending', pending_redirect=True)
check('returning from Google redirect: startup does not pre-empt it; fallback still signs in', o['anonCalls'] == 1, str(o))
# --- forgot-password mode + phone login hidden ---
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:80]))
    pg.add_init_script("window.__INITIAL_USER=null;" + FAKE); pg.goto(APP_URL); pg.wait_for_timeout(1200)
    pg.evaluate("document.getElementById('splash')?.remove(); showAuthLogin('customer')"); pg.wait_for_timeout(150)
    vis = lambda sel: pg.evaluate(f"(()=>{{const e=document.querySelector({sel!r}); return !!e && getComputedStyle(e).display!=='none' && e.offsetParent!==null;}})()")
    check('phone login entry point is hidden', not vis('#phoneAuthToggleBtn') and not vis('#phoneAuthBox'))
    pg.click("text=نسيت كلمة المرور؟"); pg.wait_for_timeout(150)
    check('forgot mode shows ONLY the email field', vis('#authEmail') and not vis('#authPassword') and not vis('#normalLoginBox .btn.google') and not vis('#authModeToggle'))
    check('forgot mode: title + button relabelled, back link shown', pg.evaluate("document.getElementById('authPanelTitle').textContent") == 'استعادة كلمة المرور' and 'إرسال رابط' in pg.evaluate("document.getElementById('sendOtp').textContent") and vis('#authResetBack'))
    pg.screenshot(path=str(ROOT / 'reset_mode.png'))
    pg.fill('#authEmail', 'mahmoud@example.com'); pg.click('#sendOtp'); pg.wait_for_timeout(400)
    calls = pg.evaluate("__auth.resetCalls")
    check('reset email: rejected continue-URL is retried without it (email actually sent)', calls == ['with-continue-url', 'plain'], str(calls))
    check('reset: clear confirmation incl. sender + Spam hint', 'Spam' in pg.evaluate("document.getElementById('authPanelSub').textContent"))
    pg.click('#authResetBack'); pg.wait_for_timeout(150)
    check('back link restores the normal login (password + Google)', vis('#authPassword') and vis('#normalLoginBox .btn.google') and pg.evaluate("document.getElementById('sendOtp').textContent") == 'تسجيل الدخول')
    pg.click("text=نسيت كلمة المرور؟"); pg.evaluate("showAuthLanding(); showAuthLogin('customer')"); pg.wait_for_timeout(100)
    check('leaving and reopening the panel never sticks in reset mode', vis('#authPassword'))
    check('no page errors', not errs, str(errs))
    b.close()
print(f"\nAUTH RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
