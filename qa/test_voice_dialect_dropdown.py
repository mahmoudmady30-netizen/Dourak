import pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent
APP_URL = ROOT.parent.joinpath('index.html').as_uri()
res = []
def check(name, ok, detail=''):
    res.append(ok)
    print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

MOCK_DB = """
window.__store = {};
window.firebase = {firestore:{FieldValue:{serverTimestamp:()=>({toMillis:()=>Date.now()})}}};
const vpColl = { where(f,op,v){ return { get: async()=>({docs:Object.entries(window.__store).filter(([id,d])=>d.lang===v).map(([id,v])=>({id,ref:{delete: async()=>{delete window.__store[id];}},data:()=>v}))}) }; },
  doc(id){ return { set: async(v)=>{ window.__store[id]=v; }, delete: async()=>{ delete window.__store[id]; } }; } };
window.dourakFB = { ready:true, db:{ collection(){ return { doc(){ return { collection(){ return vpColl; }, update: async()=>{} }; } }; } } };
localStorage.setItem('dourakBusinessId','b1'); window.setup={businessId:'b1'};
"""

with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:150]))
    pg.goto(APP_URL); pg.wait_for_timeout(600)
    pg.evaluate("document.getElementById('splash')?.remove();")
    pg.evaluate(MOCK_DB)
    pg.evaluate("window.confirm=()=>true; openVoiceRecorder();")
    pg.wait_for_timeout(300)

    labels = pg.evaluate("[...document.querySelectorAll('#vrDialectSelect option')].map(o=>({v:o.value,t:o.textContent}))")
    check('dropdown has exactly 4 entries: placeholder + 3 real options (Khaleeji removed)', len(labels) == 4, str(labels))
    check('no Khaleeji option remains anywhere', not any('خليج' in l['t'] or l['v'] == 'khaleeji' for l in labels), str(labels))
    check("Egyptian option renamed away from a person's name, marked ready", any(l['v'] == 'mohamed_tharwat' and 'المصرية' in l['t'] and 'جاهزة' in l['t'] for l in labels), str(labels))
    check('MSA (Fatima) option present and marked ready', any(l['v'] == 'fatima_msa' and 'الفصحى' in l['t'] and 'جاهزة' in l['t'] for l in labels), str(labels))
    check('English (Selene) option present and marked ready', any(l['v'] == 'selene_en' and 'جاهزة' in l['t'] for l in labels), str(labels))

    pg.evaluate("document.getElementById('vrDialectSelect').value='mohamed_tharwat'; vrDialectChanged('mohamed_tharwat');")
    pg.wait_for_timeout(500)
    store1 = pg.evaluate("Object.keys(window.__store)")
    check('choosing Egyptian writes the real recorded clips (14 keys)', sorted(store1) == sorted(['ar_'+k for k in ['prefix','a','0','1','2','3','4','5','6','7','8','9','suffix','recall']]), str(store1))

    pg.evaluate("window.confirm=()=>true; document.getElementById('vrDialectSelect').value='fatima_msa'; vrDialectChanged('fatima_msa');")
    pg.wait_for_timeout(500)
    store2 = pg.evaluate("Object.keys(window.__store)")
    check('choosing MSA writes the real Fatima clips (12 keys, no suffix/recall recorded)', sorted(store2) == sorted(['ar_'+k for k in ['prefix','a','0','1','2','3','4','5','6','7','8','9']]), str(store2))
    sizes = pg.evaluate("Object.fromEntries(Object.entries(window.__store).map(([k,v])=>[k, v.dataUrl.length]))")
    check('every MSA clip has real audio content', all(v > 500 for v in sizes.values()), str(sizes))

    # Selene: the specific bug this recording exposed — presets can be
    # under a DIFFERENT language bucket than whatever vr.lang currently
    # is (the recorder defaults to Arabic; Selene is English-only). Before
    # the fix this silently wrote nothing at all, with zero error shown.
    pg.evaluate("window.confirm=()=>true; document.getElementById('vrDialectSelect').value='selene_en'; vrDialectChanged('selene_en');")
    pg.wait_for_timeout(500)
    store3 = pg.evaluate("Object.keys(window.__store)")
    en_keys = sorted(k for k in store3 if k.startswith('en_'))
    ar_keys = sorted(k for k in store3 if k.startswith('ar_'))
    check('choosing English (Selene) from the Arabic recorder view actually writes clips (was a silent no-op bug)', en_keys == sorted(['en_'+k for k in ['prefix','a','0','1','2','3','4','5','6','7','8','9']]), str(store3))
    sizes3 = pg.evaluate("Object.fromEntries(Object.entries(window.__store).map(([k,v])=>[k, v.dataUrl.length]))")
    check('every Selene clip has real audio content', all(v > 500 for v in sizes3.values()), str(sizes3))
    check('writing the English pack leaves the separate Arabic (MSA) pack fully intact — different languages coexist', ar_keys == sorted(store2), str((ar_keys, store2)))

    check('no page errors across all dropdown paths', not errs, str(errs))
    b.close()

print(f"\nVOICE-DIALECT-DROPDOWN RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
