import pathlib, json
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent
APP_URL = ROOT.parent.joinpath('index.html').as_uri()
res = []
def check(name, ok, detail=''):
    res.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

FAKE = r"""
(() => {
  const user = { uid:'u1', email:'m@example.com', isAnonymous:true, providerData:[] };
  const auth = {
    get currentUser() { return user; },
    onAuthStateChanged(cb){ setTimeout(()=>cb(user),10); return ()=>{}; },
    setPersistence:()=>Promise.resolve(), signInAnonymously: async()=>({user}),
    getRedirectResult: async()=>({user:null}), signOut: async()=>{}
  };
  window.__setPermanent = (v) => { user.isAnonymous = !v; };
  function q(){ return { where(){return q();}, orderBy(){return this;}, limit(){return this;}, get: async()=>({docs:[],empty:true}), onSnapshot(cb){setTimeout(()=>cb({docs:[],empty:true}),0); return ()=>{};} }; }
  function col(name){ return Object.assign(q(), { doc(id){ return { get: async()=>({exists:false,data:()=>({})}), set: async()=>{}, update: async()=>{}, collection:()=>col(name) }; } }); }
  const fs = () => ({ collection: col, runTransaction: async(f)=>f({get:async()=>({exists:false,data:()=>({})}),set(){},update(){}}) });
  fs.FieldValue = { serverTimestamp: () => ({}), delete: () => ({}) };
  const a = () => auth; a.Auth = { Persistence: { LOCAL: 'local' } }; a.GoogleAuthProvider = function(){ this.setCustomParameters=()=>{}; };
  Object.defineProperty(window,'firebase',{value:{initializeApp:()=>({}),auth:a,firestore:fs,apps:[]},writable:false});
})();
"""

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width':390,'height':844}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.add_init_script(FAKE)
    pg.goto(APP_URL); pg.wait_for_timeout(900)

    # --- Guest mode: exactly what the report showed (anonymous session,
    # entered via "متابعة كضيف") ---
    pg.evaluate("document.getElementById('splash')?.remove(); enterGuestApp('customer');")
    pg.wait_for_timeout(300)
    pg.evaluate("customerGo('cProfile')")
    pg.wait_for_timeout(300)
    btn_text = pg.evaluate("document.getElementById('cProfileAuthBtn')?.textContent || ''")
    btn_onclick = pg.evaluate("document.getElementById('cProfileAuthBtn')?.getAttribute('onclick') || ''")
    check('guest mode shows "تسجيل الدخول" (login), not logout', btn_text == 'تسجيل الدخول', btn_text)
    check('guest mode button is wired to the real login flow', btn_onclick == 'goToCustomerLogin()', btn_onclick)
    check('guest mode button is NOT wired to logout()', 'logout()' not in btn_onclick, btn_onclick)

    # Tapping it in guest mode must reach the real login screen.
    pg.click('#cProfileAuthBtn'); pg.wait_for_timeout(200)
    check('tapping it in guest mode actually shows the auth screen', pg.evaluate("!document.getElementById('auth').classList.contains('hidden')"))

    # --- Real permanent customer: must show the normal logout button ---
    pg.evaluate("window.__setPermanent(true); guestMode = false;")
    pg.evaluate("document.getElementById('auth').classList.add('hidden'); document.getElementById('customer').classList.remove('hidden'); customerGo('cProfile');")
    pg.wait_for_timeout(300)
    btn_text2 = pg.evaluate("document.getElementById('cProfileAuthBtn')?.textContent || ''")
    btn_onclick2 = pg.evaluate("document.getElementById('cProfileAuthBtn')?.getAttribute('onclick') || ''")
    check('a real, permanently-signed-in customer sees "تسجيل الخروج" (logout) as normal', btn_text2 == 'تسجيل الخروج', btn_text2)
    check('real customer button is wired to logout()', btn_onclick2 == 'logout()', btn_onclick2)

    check('no page errors throughout', not errs, str(errs))
    b.close()

print(f"\nGUEST-PROFILE-BUTTON RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
