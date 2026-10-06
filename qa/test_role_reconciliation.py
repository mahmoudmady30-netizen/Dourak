from playwright.sync_api import sync_playwright
import pathlib, json
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
res = []
def check(name, ok, detail=''):
    res.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

FAKE = r"""
(() => {
  const user = { uid:'u1', email:'m@example.com', isAnonymous:false, providerData:[{providerId:'google.com'}] };
  const auth = {
    get currentUser() { return user; },
    onAuthStateChanged(cb){ setTimeout(()=>cb(user),10); return ()=>{}; },
    setPersistence:()=>Promise.resolve(),
    signInAnonymously: async()=>({user}),
    getRedirectResult: async()=>({user:null}),
    signOut: async()=>{}
  };
  window.__ownerBiz = window.__OWNS_BUSINESS ? [{ownerId:'u1'}] : [];
  function makeQuery(name, isOwnerQuery) {
    return {
      where(f, op, v) { return makeQuery(name, name === 'businesses' && f === 'ownerId'); },
      orderBy() { return this; },
      limit() { return this; },
      get: async () => ({
        empty: !(isOwnerQuery && window.__ownerBiz.length),
        docs: isOwnerQuery ? window.__ownerBiz.map(d => ({ id: 'b1', data: () => d })) : []
      }),
      onSnapshot(cb) { setTimeout(() => cb({ docs: [], empty: true }), 0); return () => {}; }
    };
  }
  function col(name) {
    return Object.assign(makeQuery(name, false), {
      doc(id) { return { get: async()=>({exists:false,data:()=>({})}), set: async()=>{}, update: async()=>{}, collection:()=>col(name) }; }
    });
  }
  const fs = () => ({ collection: col, runTransaction: async(f)=>f({get:async()=>({exists:false,data:()=>({})}),set(){},update(){}}) });
  fs.FieldValue = { serverTimestamp: () => ({}), delete: () => ({}) };
  const a = () => auth; a.Auth = { Persistence: { LOCAL: 'local' } }; a.GoogleAuthProvider = function(){ this.setCustomParameters=()=>{}; };
  Object.defineProperty(window,'firebase',{value:{initializeApp:()=>({}),auth:a,firestore:fs,apps:[]},writable:false});
})();
"""

def run(owns_business, existing_customer_profile, tb_role):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width':390,'height':844}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
        init = f"window.__OWNS_BUSINESS={str(owns_business).lower()};"
        init += f"localStorage.setItem('tbUser', {json.dumps(json.dumps({'uid':'u1','role':tb_role,'email':'m@example.com','provider':'google.com'}))});"
        if existing_customer_profile:
            init += "localStorage.setItem('tbCustomerProfile', JSON.stringify({name:'محمود',governorate:'دبي',phone:'0501234567'}));"
        pg.add_init_script(init + FAKE)
        pg.goto(APP_URL); pg.wait_for_timeout(1800)
        out = {
            'confirmSheetShown': pg.evaluate("document.getElementById('sheet')?.textContent.includes('نفس الحساب ده مستخدم بالفعل كعميل') || false"),
            'onOwnerScreen': pg.evaluate("!document.getElementById('owner').classList.contains('hidden')"),
            'bannerText': pg.evaluate("document.getElementById('customerOwnerBanner')?.textContent || ''"),
            'errs': errs,
        }
        b.close(); return out

o1 = run(owns_business=False, existing_customer_profile=True, tb_role='owner')
check('existing customer taps "owner" (no business yet): confirmation shown, not silently pushed into setup', o1['confirmSheetShown'] is True, str(o1))
check('no page errors (case 1)', not o1['errs'], str(o1['errs']))

o2 = run(owns_business=False, existing_customer_profile=False, tb_role='owner')
check('genuine new owner (no customer profile at all): zero extra friction, no confirmation dialog', o2['confirmSheetShown'] is False, str(o2))

o3 = run(owns_business=True, existing_customer_profile=True, tb_role='customer')
check('customer session, but this account owns a business: dashboard banner appears', 'لوحة التحكم' in o3['bannerText'], str(o3))
check('no page errors (case 3)', not o3['errs'], str(o3['errs']))

o4 = run(owns_business=False, existing_customer_profile=True, tb_role='customer')
check('ordinary customer with no business anywhere: no banner shown at all', o4['bannerText'] == '', str(o4))

print(f"\nROLE-RECONCILIATION RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
