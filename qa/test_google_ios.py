import pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent; APP_URL = ROOT.parent.joinpath('index.html').as_uri(); res = []
def check(name, ok, detail=''): res.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))
IPHONE = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1'
ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36'
FAKE_FIREBASE = r"""
(() => { const S = window.__auth = { log: [], user: { uid: 'anon1', isAnonymous: true, providerData: [] }, cbs: [] };
  const withLink = (u) => Object.assign(u, { linkWithCredential: async (c) => { S.log.push('linkWithCredential'); if (window.__LINK_CONFLICT) { const e = new Error('in use'); e.code = 'auth/credential-already-in-use'; e.credential = c; throw e; } S.user = withLink({ uid: 'anon1', isAnonymous: false, email: 'm@gmail.com', providerData: [{ providerId: 'google.com' }] }); return { user: S.user }; },
    linkWithPopup: async () => { S.log.push('linkWithPopup'); return { user: S.user }; } });
  withLink(S.user);
  const auth = { get currentUser() { return S.user; }, onAuthStateChanged(cb) { S.cbs.push(cb); setTimeout(() => cb(S.user), 30); return () => {}; }, setPersistence: () => Promise.resolve(),
    signInAnonymously: async () => ({ user: S.user }), getRedirectResult: async () => ({ user: null }),
    signInWithCredential: async (c) => { S.log.push('signInWithCredential:' + c.accessToken); S.user = withLink({ uid: 'google-existing', isAnonymous: false, email: 'm@gmail.com', providerData: [{ providerId: 'google.com' }] }); return { user: S.user }; },
    signInWithPopup: async () => { S.log.push('signInWithPopup'); return { user: S.user }; }, signOut: async () => {} };
  const doc = () => ({ set: async () => {}, get: async () => ({ exists: false, data: () => ({}) }), update: async () => {}, collection: () => col() });
  const col = () => ({ doc, where: () => col(), orderBy: () => col(), limit: () => col(), get: async () => ({ docs: [], empty: true }), onSnapshot: () => () => {} });
  const fs = () => ({ collection: col, runTransaction: async (f) => f({ get: async () => ({ exists: false, data: () => ({}) }), set() {}, update() {} }) });
  fs.FieldValue = { serverTimestamp: () => ({}), delete: () => ({}) };
  const a = () => auth; a.Auth = { Persistence: { LOCAL: 'local' } };
  a.GoogleAuthProvider = function () { this.setCustomParameters = () => {}; }; a.GoogleAuthProvider.credential = (id, at) => ({ providerId: 'google.com', accessToken: at });
  a.EmailAuthProvider = { credential: () => ({}) };
  Object.defineProperty(window, 'firebase', { value: { initializeApp: () => ({}), auth: a, firestore: fs, apps: [] }, writable: false });
})();
"""
# Fake Google Identity Services, served at the real URL the app loads.
FAKE_GIS = r"""window.google = { accounts: { oauth2: { initTokenClient(cfg) { window.__gis = { cfg, calls: 0 };
  return { requestAccessToken(o) { window.__gis.calls++; window.__gis.prompt = o && o.prompt; window.__gis.syncInTap = !!window.__inTap;
    setTimeout(() => window.__GIS_CANCEL ? (cfg.error_callback && cfg.error_callback({ type: 'popup_closed' })) : cfg.callback({ access_token: 'gtoken-123' }), 50); } }; } } } };"""
def run(ua, client_id='123-abc.apps.googleusercontent.com', conflict=False, cancel=False):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(user_agent=ua, viewport={'width': 390, 'height': 844}); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)[:90]))
        pg.route('https://accounts.google.com/gsi/client', lambda r: r.fulfill(status=200, content_type='application/javascript', body=FAKE_GIS))
        pg.add_init_script(f"window.DOURAK_GOOGLE_WEB_CLIENT_ID={client_id!r}; window.__LINK_CONFLICT={str(conflict).lower()}; window.__GIS_CANCEL={str(cancel).lower()};" + FAKE_FIREBASE)
        pg.goto(APP_URL); pg.wait_for_timeout(900)
        pg.evaluate("document.getElementById('splash')?.remove(); showAuthLogin('customer')")
        # mark "inside the tap" around the real click handler to prove no await precedes the popup
        pg.evaluate("document.querySelector('#normalLoginBox .btn.google').addEventListener('click',()=>{window.__inTap=true;setTimeout(()=>window.__inTap=false,0)},{capture:true})")
        pg.click('#normalLoginBox .btn.google'); busy = pg.evaluate("document.querySelector('#normalLoginBox .btn.google').textContent")
        pg.wait_for_timeout(700)
        out = pg.evaluate("({gis: window.__gis ? {calls: __gis.calls, prompt: __gis.prompt, sync: __gis.syncInTap, scope: __gis.cfg.scope} : null, log: __auth.log, user: __auth.user.uid, anon: __auth.user.isAnonymous, btn: document.querySelector('#normalLoginBox .btn.google').textContent, btnDisabled: document.querySelector('#normalLoginBox .btn.google').disabled})")
        b.close(); out['busy'] = busy; out['errs'] = errs; return out
o = run(IPHONE)
check('iPhone: Google own popup opened directly inside the tap', o['gis'] and o['gis']['calls'] == 1 and o['gis']['sync'] is True, str(o['gis']))
check('iPhone: account chooser requested (select_account)', o['gis'] and o['gis']['prompt'] == 'select_account')
check('iPhone: button shows a loading state while signing in', 'جاري تسجيل الدخول' in o['busy'], o['busy'])
check('iPhone: guest session upgraded to the Google account (same user)', o['log'] == ['linkWithCredential'] and o['user'] == 'anon1' and o['anon'] is False, str(o['log']))
check('iPhone: Firebase popup NOT used (the part Safari breaks)', 'signInWithPopup' not in o['log'] and 'linkWithPopup' not in o['log'])
check('iPhone: no page errors', not o['errs'], str(o['errs']))
o = run(IPHONE, conflict=True)
check('iPhone, existing Google account: signs into it', o['log'] == ['linkWithCredential', 'signInWithCredential:gtoken-123'] and o['user'] == 'google-existing', str(o['log']))
o = run(IPHONE, cancel=True)
check('iPhone, popup closed: button restored, nothing signed in', o['btnDisabled'] is False and 'Google' in o['btn'] and o['anon'] is True, o['btn'])
o = run(ANDROID)
check('Android: unchanged — normal Firebase popup path', o['gis'] is not None and o['gis']['calls'] == 0 and 'linkWithPopup' in o['log'], str(o['log']))
o = run(IPHONE, client_id='')
check('iPhone, no Client ID passed to run(): app default takes over, still works', o['gis'] is not None and o['anon'] is False, str(o))
def run_forced_empty(ua):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(user_agent=ua); errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)[:90]))
        pg.route('https://accounts.google.com/gsi/client', lambda r: r.fulfill(status=200, content_type='application/javascript', body=FAKE_GIS))
        pg.add_init_script("window.__LINK_CONFLICT=false; window.__GIS_CANCEL=false;" + FAKE_FIREBASE + "window.addEventListener('DOMContentLoaded',()=>{window.DOURAK_GOOGLE_WEB_CLIENT_ID='';});")
        pg.goto(APP_URL); pg.wait_for_timeout(900); pg.evaluate("document.getElementById('splash')?.remove(); showAuthLogin('customer')")
        pg.click('#normalLoginBox .btn.google'); pg.wait_for_timeout(500)
        out = pg.evaluate("({log: __auth.log, errs: []})"); out['errs'] = errs; b.close(); return out
o2 = run_forced_empty(IPHONE)
check('iPhone, Client ID genuinely empty: falls back to Firebase popup path, no crash', not o2['errs'] and 'linkWithPopup' in o2['log'], str(o2))
print(f"\nGOOGLE-iOS RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
