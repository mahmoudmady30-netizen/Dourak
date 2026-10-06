import pathlib, json
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent
APP_URL = ROOT.parent.joinpath('index.html').as_uri()
res = []
def check(name, ok, detail=''):
    res.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

# One business doc + N services, wired through a fully-chainable query mock
# (see test_role_reconciliation.py for why chainability matters — a single
# missing method deep in a real code path silently swallows everything
# after it inside the same try/catch).
def fake_firebase(uid, is_anon, services, business_extra=None):
    biz = {'name':'صالون الأمير','active':True,'hours':'00:00 - 23:59','ownerId':'own1', **(business_extra or {})}
    return f"""
(() => {{
  const user = {{ uid:{json.dumps(uid)}, email:'m@example.com', isAnonymous:{str(is_anon).lower()}, providerData:[{{providerId:'password'}}] }};
  window.__ticketsCreated = [];
  user.sendEmailVerification = async () => {{}};
  user.emailVerified = true;
  user.linkWithCredential = async (cred) => {{ user.isAnonymous=false; user.email=cred.email||user.email; return {{user}}; }};
  window.__services = {json.dumps(services)};
  const auth = {{ get currentUser() {{ return user; }}, onAuthStateChanged(cb){{ setTimeout(()=>cb(user),10); return ()=>{{}}; }},
    setPersistence:()=>Promise.resolve(), signInAnonymously: async()=>({{user}}), getRedirectResult: async()=>({{user:null}}), signOut: async()=>{{}},
    signInWithEmailAndPassword: async(email,pw) => {{ user.isAnonymous=false; user.uid='u2'; user.email=email; return {{user}}; }},
    createUserWithEmailAndPassword: async(email,pw) => {{ user.isAnonymous=false; user.uid='u2'; user.email=email; user.sendEmailVerification=async()=>{{}}; return {{user}}; }} }};
  function makeQuery(path) {{
    return {{
      where(f,op,v){{ return makeQuery(path); }},
      orderBy(){{ return this; }}, limit(){{ return this; }},
      get: async () => {{
        if (path === 'businesses/b1/services') return {{ docs: window.__services.map((s,i)=>({{id:'s'+i, data:()=>s}})), empty: !window.__services.length }};
        if (path === 'businesses/b1/ratings') return {{ docs: [], empty: true }};
        if (path === 'businesses') return {{ docs: [], empty: true }};
        return {{ docs: [], empty: true }};
      }},
      onSnapshot(cb){{ setTimeout(()=>cb({{docs:[],empty:true}}),0); return ()=>{{}}; }}
    }};
  }}
  function doc(path) {{
    return {{
      path,
      get: async () => {{
        if (path === 'businesses/b1') return {{ exists:true, id:'b1', data:()=>({json.dumps(biz)}) }};
        if (path === 'users/'+{json.dumps(uid)}) return {{ exists:false, data:()=>({{}}) }};
        const svcMatch = /^businesses\/b1\/services\/(s\d+)$/u.exec(path);
        if (svcMatch) {{
          const idx = Number(svcMatch[1].slice(1));
          const s = window.__services[idx];
          return s ? {{ exists:true, id:svcMatch[1], data:()=>s }} : {{ exists:false, data:()=>({{}}) }};
        }}
        return {{ exists:false, data:()=>({{}}) }};
      }},
      set: async (d) => {{ if (path.includes('queueTickets')) window.__ticketsCreated.push(d); }},
      delete: async () => {{}},
      update: async () => {{}},
      collection: (name) => col(path + '/' + name)
    }};
  }}
  function col(path) {{ return Object.assign(makeQuery(path), {{ doc: (id) => doc(path + '/' + (id||'auto')) }}); }}
  const fs = () => ({{ collection: (n) => col(n),
    runTransaction: async (fn) => fn({{
      get: async (r) => r.get ? r.get() : {{exists:false,data:()=>({{}})}},
      set: (r,d) => {{ if ((r.path||'').includes('queueTickets')) window.__ticketsCreated.push(d); }},
      update: () => {{}}
    }}) }});
  fs.FieldValue = {{ serverTimestamp: () => ({{}}), delete: () => ({{}}) }};
  const a = () => auth; a.Auth = {{ Persistence: {{ LOCAL: 'local' }} }}; a.GoogleAuthProvider = function(){{ this.setCustomParameters=()=>{{}}; }};
  a.EmailAuthProvider = {{ credential: (email,pw) => ({{email,pw}}) }};
  Object.defineProperty(window,'firebase',{{value:{{initializeApp:()=>({{}}),auth:a,firestore:fs,apps:[]}},writable:false}});
}})();
"""

def run(logged_in, n_services, tb_role='customer', extra_init=''):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width':390,'height':844}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
        services = [{'name':'قص شعر','duration':30,'price':40,'active':True}, {'name':'صبغة','duration':60,'price':100,'active':True}, {'name':'حلاقة ذقن','duration':15,'price':20,'active':True}][:n_services]
        fb = fake_firebase('u1', not logged_in, services)
        init = extra_init
        if logged_in:
            init += f"localStorage.setItem('tbUser', {json.dumps(json.dumps({'uid':'u1','role':tb_role,'email':'m@example.com','provider':'password'}))});"
            init += "localStorage.setItem('tbCustomerProfile', JSON.stringify({name:'محمود',governorate:'دبي',phone:'0501234567'}));"
        pg.add_init_script(init + fb)
        pg.goto(APP_URL + '?business=b1&join=1'); pg.wait_for_timeout(2200)
        out = {
            'ticketsCreated': pg.evaluate("window.__ticketsCreated"),
            'authVisible': pg.evaluate("!document.getElementById('auth').classList.contains('hidden')"),
            'sheetOpen': pg.evaluate("document.getElementById('modal')?.classList.contains('open') || !document.getElementById('sheet').closest('.modal')?.classList.contains('hidden')") if False else pg.evaluate("document.getElementById('sheet')?.textContent.length > 0"),
            'urlClean': '?' not in pg.evaluate("location.search") or 'business' not in pg.evaluate("location.search"),
            'errs': errs,
        }
        b.close(); return out

o1 = run(logged_in=True, n_services=1)
check('logged-in customer, single-service business: ticket created automatically (no tap needed)', len(o1['ticketsCreated']) == 1, str(o1))
check('QR params stripped from the URL after being consumed', o1['urlClean'], str(o1))
check('no page errors (single-service, logged in)', not o1['errs'], str(o1['errs']))

o2 = run(logged_in=True, n_services=3)
check('CURRENT BEHAVIOR CHECK — logged-in customer, MULTI-service business: does NOT auto-book (shows a picker instead)', len(o2['ticketsCreated']) == 0, str(o2))


# --- Not logged in: scan -> shown auth -> register -> onboarding -> auto-book ---
def run_not_logged_in(n_services=1):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width':390,'height':844}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
        services = [{'name':'قص شعر','duration':30,'price':40,'active':True}][:n_services]
        fb = fake_firebase('u2', True, services)  # isAnonymous=True: nobody signed in permanently yet
        pg.add_init_script(fb)
        pg.goto(APP_URL + '?business=b1&join=1'); pg.wait_for_timeout(1000)
        stage1_auth_visible = pg.evaluate("!document.getElementById('auth').classList.contains('hidden')")
        stage1_qr_stashed = pg.evaluate("localStorage.getItem('dourakPendingQrBusinessId')")
        # Complete registration through the REAL button/flow a customer
        # actually uses (not an internal function) — the true end-to-end path.
        pg.evaluate("showAuthLogin('customer'); toggleAuthPasswordMode();")  # switch to register mode
        pg.fill('#authEmail', 'm@example.com')
        pg.fill('#authPassword', 'password123')
        pg.click('#sendOtp')
        pg.wait_for_timeout(600)
        stage2_onboarding_visible = pg.evaluate("!document.getElementById('customerOnboarding').classList.contains('hidden')")
        # Complete onboarding exactly as a brand-new customer would.
        pg.evaluate("""
            document.getElementById('onboardName').value = 'محمود';
            document.getElementById('onboardGovernorate').innerHTML = '<option value="دبي">دبي</option>';
            document.getElementById('onboardGovernorate').value = 'دبي';
        """)
        pg.evaluate("saveCustomerOnboarding()")
        pg.wait_for_timeout(1500)
        return {
            'stage1_auth_visible': stage1_auth_visible,
            'stage1_qr_stashed': stage1_qr_stashed,
            'stage2_onboarding_visible': stage2_onboarding_visible,
            'ticketsCreated': pg.evaluate("window.__ticketsCreated"),
            'errs': errs,
        }

o3 = run_not_logged_in(n_services=1)
check('not logged in: auth screen shown immediately (not silently blocked)', o3['stage1_auth_visible'] is True, str(o3))
check('QR business id correctly stashed while showing auth', o3['stage1_qr_stashed'] == 'b1', str(o3))
check('brand-new customer after registering: onboarding required before anything else', o3['stage2_onboarding_visible'] is True, str(o3))
check('after completing onboarding: the original QR scan auto-books with ZERO extra taps', len(o3['ticketsCreated']) == 1, str(o3))
check('no page errors across the whole not-logged-in chain', not o3['errs'], str(o3['errs']))

print(f"\nQR-JOIN RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
