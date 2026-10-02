import pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent
APP_URL = ROOT.parent.joinpath('index.html').as_uri()
res = []
def check(name, ok, detail=''):
    res.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

def fake_firebase(uid):
    return f"""
(() => {{
  const user = {{ uid:{uid!r}, isAnonymous:false, providerData:[{{providerId:'password'}}] }};
  const auth = {{ get currentUser() {{ return user; }}, onAuthStateChanged(cb){{ setTimeout(()=>cb(user),10); return ()=>{{}}; }},
    setPersistence:()=>Promise.resolve(), signInAnonymously: async()=>({{user}}), getRedirectResult: async()=>({{user:null}}), signOut: async()=>{{}} }};
  function q(){{ return {{ where(){{return q();}}, orderBy(){{return this;}}, limit(){{return this;}}, get: async()=>({{docs:[],empty:true}}), onSnapshot(cb){{setTimeout(()=>cb({{docs:[],empty:true}}),0); return ()=>{{}};}} }}; }}
  function col(name){{ return Object.assign(q(), {{ doc(id){{ return {{
    get: async()=>{{ if (name==='businesses' && id==='b1') return {{exists:true, id:'b1', data:()=>({{name:'صالون الأمير', ownerId:'REAL_OWNER_UID', active:true, hours:'00:00 - 23:59'}})}}; return {{exists:false,data:()=>({{}})}}; }},
    set: async()=>{{}}, update: async()=>{{}}, collection:()=>col(name),
    onSnapshot(cb){{ setTimeout(()=>cb({{exists:false,data:()=>({{}})}}),0); return ()=>{{}}; }} }}; }} }}); }}
  const fs = () => ({{ collection: col, runTransaction: async(f)=>f({{get:async()=>({{exists:false,data:()=>({{}})}}),set(){{}},update(){{}}}}) }});
  fs.FieldValue = {{ serverTimestamp: () => ({{}}), delete: () => ({{}}) }};
  const a = () => auth; a.Auth = {{ Persistence: {{ LOCAL: 'local' }} }}; a.GoogleAuthProvider = function(){{ this.setCustomParameters=()=>{{}}; }};
  Object.defineProperty(window,'firebase',{{value:{{initializeApp:()=>({{}}),auth:a,firestore:fs,apps:[]}},writable:false}});
}})();
"""

def run(uid):
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width':390,'height':500}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
        pg.add_init_script(fake_firebase(uid))
        pg.goto(APP_URL + '?display=b1'); pg.wait_for_timeout(1500)
        out = {
            'displayVisible': pg.evaluate("!document.getElementById('publicDisplay').classList.contains('hidden')"),
            'message': pg.evaluate("document.getElementById('pdLayout')?.textContent || ''"),
            'errs': errs,
        }
        b.close(); return out

o_real_owner = run('REAL_OWNER_UID')
check('the actual owner (uid matches ownerId) reaches the real, fully working display', 'LIVE' in o_real_owner['message'] and 'مخصصة لصاحب المكان' not in o_real_owner['message'], str(o_real_owner))
check('no page errors for the real owner', not o_real_owner['errs'], str(o_real_owner['errs']))

o_staff = run('SOME_STAFF_UID')
check('a different signed-in identity (e.g. staff) is blocked with the owner-only message', 'مخصصة لصاحب المكان' in o_staff['message'], str(o_staff))
check('blocked visitor does NOT get the real queue layout rendered', o_staff['displayVisible'] is True and 'مخصصة' in o_staff['message'], str(o_staff))
check('no page errors when blocking a non-owner', not o_staff['errs'], str(o_staff['errs']))

print(f"\nDISPLAY-OWNER-ONLY RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
