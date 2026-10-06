import pathlib
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
from playwright.sync_api import sync_playwright
res = []
def check(name, ok, detail=''): res.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))
MOCK_DB = """
window.__store = {};
window.firebase = {firestore:{FieldValue:{serverTimestamp:()=>({toMillis:()=>Date.now()})}}};
const vpColl = { where(){ return { get: async()=>({docs:Object.entries(window.__store).map(([id,v])=>({id,data:()=>v}))}) }; },
  doc(id){ return { set: async(v)=>{ window.__store[id]=v; }, delete: async()=>{ delete window.__store[id]; } }; } };
window.dourakFB = { ready:true, db:{ collection(){ return { doc(){ return { collection(){ return vpColl; }, update: async()=>{} }; } }; } } };
localStorage.setItem('dourakBusinessId','b1'); window.setup={businessId:'b1'}; window.__dourakDisplayBid='b1';
"""
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(); errs=[]
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(APP_URL); pg.wait_for_timeout(600)
    pg.evaluate("document.getElementById('splash')?.remove();"); pg.evaluate(MOCK_DB)
    pg.evaluate("window.confirm=()=>true;")  # in case of an old-clips prompt
    pg.evaluate("openVoiceRecorder()"); pg.wait_for_timeout(300)
    # Superseded UI: the flat list of preset buttons became a single
    # dialect dropdown (test_voice_dialect_dropdown.py covers that UI and
    # its other 3 options directly) — updated here to keep exercising
    # this file's own byte-level distinctness checks below.
    check('dialect dropdown offers the Egyptian option', pg.evaluate("[...document.querySelectorAll('#vrDialectSelect option')].some(o => o.value === 'mohamed_tharwat')"))
    pg.evaluate("document.getElementById('vrDialectSelect').value='mohamed_tharwat'; vrDialectChanged('mohamed_tharwat');")
    pg.wait_for_timeout(500)
    prog = pg.evaluate("document.querySelector('.vr-progress')?.textContent") or ''
    check('applying it fills all 12 required clips in one tap — voice is now complete', '12 / 12' in prog and 'جاهز للتلفزيون' in prog, prog)
    store = sorted(pg.evaluate("Object.keys(window.__store)"))
    check('exactly the 14 recorded clips were written (prefix+a+0-9+suffix+recall)', store == sorted(['ar_'+k for k in ['prefix','a','0','1','2','3','4','5','6','7','8','9','suffix','recall']]), str(store))
    sizes = pg.evaluate("Object.fromEntries(Object.entries(window.__store).map(([k,v])=>[k, v.dataUrl.length]))")
    check('every clip has real audio content (not empty/placeholder)', all(v > 500 for v in sizes.values()), str(sizes))
    urls = pg.evaluate("Object.fromEntries(Object.entries(window.__store).map(([k,v])=>[k, v.dataUrl]))")
    check('"0" and "1" are distinct recordings, not duplicated by mistake (same size is coincidence — checking actual bytes)', urls['ar_0'] != urls['ar_1'], 'sizes happened to match: ' + str((sizes['ar_0'], sizes['ar_1'])))
    check('no missing-clip warning anymore (nothing left to be missing)', 'صفر' not in pg.evaluate("document.getElementById('toast')?.textContent||''"))
    pg.evaluate("closeModal()")
    b.close()
print(f"\nVOICE-PRESET RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
