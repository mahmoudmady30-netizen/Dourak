from playwright.sync_api import sync_playwright
import pathlib
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'
# Simulates the ACTUAL origin_mismatch failure mode: requestAccessToken()
# opens a popup that navigates to a real Google error page — neither
# callback nor error_callback ever fires. That's the exact case the
# timeout has to catch.
STUCK_GIS = """window.google = { accounts: { oauth2: { initTokenClient(cfg) { window.__gisCfg = cfg;
  return { requestAccessToken() { window.__requested = (window.__requested||0) + 1; /* stuck forever, like the real bug */ } }; } } } };"""
FAKE_FIREBASE = r"""
(() => { const S = window.__auth = { log: [] };
  const auth = { get currentUser() { return { uid:'anon1', isAnonymous:true, providerData:[], linkWithPopup: async () => { S.log.push('linkWithPopup'); return { user: { uid:'anon1' } }; } }; },
    onAuthStateChanged(cb) { setTimeout(() => cb(this.currentUser), 20); return () => {}; }, setPersistence: () => Promise.resolve(),
    signInAnonymously: async () => ({ user: this.currentUser }), getRedirectResult: async () => ({ user: null }), signOut: async () => {} };
  const doc = () => ({ set: async () => {}, get: async () => ({ exists: false, data: () => ({}) }), update: async () => {}, collection: () => col() });
  const col = () => ({ doc, where: () => col(), orderBy: () => col(), limit: () => col(), get: async () => ({ docs: [], empty: true }), onSnapshot: () => () => {} });
  const fs = () => ({ collection: col, runTransaction: async (f) => f({ get: async () => ({ exists: false, data: () => ({}) }), set() {}, update() {} }) });
  fs.FieldValue = { serverTimestamp: () => ({}), delete: () => ({}) };
  const a = () => auth; a.Auth = { Persistence: { LOCAL: 'local' } }; a.GoogleAuthProvider = function () { this.setCustomParameters = () => {}; };
  Object.defineProperty(window, 'firebase', { value: { initializeApp: () => ({}), auth: a, firestore: fs, apps: [] }, writable: false });
})();
"""
res = []
def check(name, ok, detail=''): res.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(user_agent=IPHONE, viewport={'width': 390, 'height': 844}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:100]))
    pg.route('https://accounts.google.com/gsi/client', lambda r: r.fulfill(status=200, content_type='application/javascript', body=STUCK_GIS))
    pg.add_init_script("window.DOURAK_GOOGLE_WEB_CLIENT_ID='123.apps.googleusercontent.com';" + FAKE_FIREBASE)
    pg.goto(APP_URL); pg.wait_for_timeout(900)
    pg.evaluate("document.getElementById('splash')?.remove(); showAuthLogin('customer')")
    pg.click('#normalLoginBox .btn.google'); pg.wait_for_timeout(200)
    busy_text = pg.evaluate("document.querySelector('#normalLoginBox .btn.google').textContent")
    check('button shows loading state right after the tap (popup opened)', 'جاري تسجيل الدخول' in busy_text, busy_text)
    check("Google's requestAccessToken was actually called (this is the stuck popup)", pg.evaluate("window.__requested") == 1)
    pg.wait_for_timeout(500)
    still_busy = pg.evaluate("document.querySelector('#normalLoginBox .btn.google').disabled")
    check('before the 10s timeout: button is still (correctly) waiting', still_busy is True)
    pg.wait_for_timeout(10200)  # cross the 10s safety-net threshold
    recovered = pg.evaluate("document.querySelector('#normalLoginBox .btn.google').disabled")
    check('after 10s stuck with zero callback: button is un-stuck automatically', recovered is False)
    toast = pg.evaluate("document.getElementById('toast')?.textContent || ''")
    check('a clear message is shown instead of silence', 'Google' in toast or 'جرّب' in toast, toast)
    check('automatically falls back to the Firebase flow (not left completely dead)', 'linkWithPopup' in pg.evaluate("__auth.log"), str(pg.evaluate("__auth.log")))
    check('no page errors', not errs, str(errs))
    b.close()
print(f"\nGIS-STUCK-RECOVERY RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
