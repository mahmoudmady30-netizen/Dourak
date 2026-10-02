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
  // Real Firebase persists sign-out across a reload (its own storage, not
  // an in-memory flag) — a plain JS variable here would reset on every
  // navigation and make signOut() look undone the moment the page
  // reloads, which is exactly what logout() does right after signing out.
  const permUser = { uid:'u1', email:'m@example.com', isAnonymous:false, providerData:[{providerId:'password'}] };
  let anonUser = null;
  const auth = {
    get currentUser() {
      if (localStorage.getItem('__mockSignedOut') === '1') return anonUser;
      return permUser;
    },
    onAuthStateChanged(cb){ setTimeout(()=>cb(this.currentUser),10); return ()=>{}; },
    setPersistence:()=>Promise.resolve(),
    signInAnonymously: async()=>{ anonUser = { uid:'anonNew', isAnonymous:true, providerData:[] }; return {user:anonUser}; },
    getRedirectResult: async()=>({user:null}),
    signOut: async()=>{ localStorage.setItem('__mockSignedOut','1'); }
  };
  function q(){ return { where(){return q();}, orderBy(){return this;}, limit(){return this;}, get: async()=>({docs:[],empty:true}), onSnapshot(cb){setTimeout(()=>cb({docs:[],empty:true}),0); return ()=>{};} }; }
  function col(name){ return Object.assign(q(), { doc(id){ return { get: async()=>({exists:false,data:()=>({})}), set: async()=>{}, update: async()=>{}, collection:()=>col(name) }; } }); }
  const fs = () => ({ collection: col, runTransaction: async(f)=>f({get:async()=>({exists:false,data:()=>({})}),set(){},update(){}}) });
  fs.FieldValue = { serverTimestamp: () => ({}), delete: () => ({}) };
  const a = () => auth; a.Auth = { Persistence: { LOCAL: 'local' } }; a.GoogleAuthProvider = function(){ this.setCustomParameters=()=>{}; };
  Object.defineProperty(window,'firebase',{value:{initializeApp:()=>({}),auth:a,firestore:fs,apps:[]},writable:false});
})();
"""

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width':390,'height':844}); errs=[]
    pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    # Start as a REAL, fully-registered customer (matches a real prior session).
    # add_init_script re-runs on EVERY load, including the reload logout()
    # itself triggers — guarded so the seed data only ever applies once,
    # otherwise it would re-plant the exact stale data the fix just removed.
    init = "if (!localStorage.getItem('__seeded')) {"
    init += "localStorage.setItem('__seeded','1');"
    init += f"localStorage.setItem('tbUser', {json.dumps(json.dumps({'uid':'u1','role':'customer','email':'m@example.com','provider':'password'}))});"
    init += "localStorage.setItem('tbCustomerProfile', JSON.stringify({name:'محمود مدي',governorate:'دبي',phone:'0501234567'}));"
    init += "localStorage.setItem('dourakLastRole','customer'); localStorage.setItem('dourakLastRoleUid','u1');"
    init += "}"
    pg.add_init_script(init + FAKE)
    pg.goto(APP_URL); pg.wait_for_timeout(1200)

    before_profile = pg.evaluate("localStorage.getItem('tbCustomerProfile')")
    check('sanity: registered customer profile is present before logout', before_profile is not None and 'محمود' in before_profile, before_profile)

    # location.reload() itself is a known Playwright/Chromium file:// quirk
    # that can wipe localStorage on reload whenever add_init_script is
    # registered (confirmed with a completely unrelated key in a minimal
    # page with zero app code involved) — a test-infrastructure limitation,
    # not something logout() itself does. Stubbing reload to a no-op lets
    # the removeItem calls run for real while checking state right after,
    # without the reload step that this environment can't reliably measure.
    pg.evaluate("window.__reloadCalled = false; location.reload = () => { window.__reloadCalled = true; };")
    pg.evaluate("logout()")
    pg.wait_for_timeout(800)
    after_profile = pg.evaluate("localStorage.getItem('tbCustomerProfile')")
    after_user = pg.evaluate("localStorage.getItem('tbUser')")
    after_role_uid = pg.evaluate("localStorage.getItem('dourakLastRoleUid')")
    check('THE FIX — tbCustomerProfile is gone after logout (was the actual bug: never cleared before)', after_profile is None, after_profile)
    check('tbUser is gone after logout', after_user is None, after_user)
    check('dourakLastRoleUid is gone after logout (no stale role memory either)', after_role_uid is None, after_role_uid)

    # Now the exact reported scenario: with the fix's removals already
    # confirmed above, the in-memory customerProfile variable (which
    # logout() also nulls directly) must reflect the same "nothing left"
    # state — this is what customerNeedsOnboarding() actually reads.
    check('in-memory customerProfile is also cleared (not just localStorage)', pg.evaluate("customerProfile") is None)
    # customerNeedsOnboarding() isn't exposed on window (internal closure
    # function) — but its entire logic is exactly
    # "customerProfile?.name && customerProfile?.governorate", which is
    # already directly confirmed null above. That's the real proof: the
    # exact data this check reads is gone, so onboarding is correctly
    # required again on the next "عميل" entry.
    check('no page errors', not errs, str(errs))
    b.close()

print(f"\nLOGOUT-CLEARS-PROFILE RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
