import os, pathlib
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
from playwright.sync_api import sync_playwright
import json
OVERFLOW = """() => { const vw=innerWidth, out=[]; document.querySelectorAll('body *').forEach(el=>{ const cs=getComputedStyle(el); if(cs.display==='none'||cs.visibility==='hidden'||el.closest('.hidden')) return; const r=el.getBoundingClientRect(); if(r.width>0 && (r.right>vw+2 || r.left< -2)){ let p=el.parentElement, clipped=false; while(p){ const ps=getComputedStyle(p); if(/(auto|scroll)/.test(ps.overflowX)){clipped=true;break;} p=p.parentElement;} if(!clipped) out.push((el.id?'#'+el.id:el.tagName.toLowerCase()+'.'+[...el.classList].slice(0,2).join('.'))+' r='+Math.round(r.right)); } }); return {docOverflow: document.documentElement.scrollWidth-vw, items:[...new Set(out)].slice(0,4)}; }"""
with sync_playwright() as p:
    b=p.chromium.launch(); report={}
    for w in [320,375,768,1280]:
        pg=b.new_page(viewport={'width':w,'height':800}); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)[:120]))
        pg.add_init_script("localStorage.setItem('tbSetup', JSON.stringify({businessId:'b1',name:'صالون الأمير للحلاقة والتجميل',address:'دبي مارينا',hours:'10:00 - 22:00',maxQueueCapacity:10,lastTokenTime:'21:00'})); localStorage.setItem('dourakBusinessId','b1');")
        pg.goto(APP_URL); pg.wait_for_timeout(700)
        pg.evaluate("document.getElementById('splash')?.remove()")
        screens=[('auth-landing',"showAuthLanding()"),('auth-login',"showAuthLogin('customer')")]
        oids=pg.evaluate("[...document.querySelectorAll('#owner .screen')].map(s=>s.id)")
        cids=pg.evaluate("[...document.querySelectorAll('#customer .screen')].map(s=>s.id)")
        res={}
        for name,js in screens:
            pg.evaluate("['owner','customer'].forEach(i=>document.getElementById(i).classList.add('hidden'));document.getElementById('auth').classList.remove('hidden');"+js); pg.wait_for_timeout(150)
            res[name]=pg.evaluate(OVERFLOW)
        pg.evaluate("document.getElementById('auth').classList.add('hidden');document.getElementById('owner').classList.remove('hidden');window.role='owner'")
        for sid in oids:
            try: pg.evaluate(f"ownerGo('{sid}')")
            except Exception as e: errs.append(f'ownerGo({sid}) threw: {str(e)[:80]}')
            pg.wait_for_timeout(120); res['owner:'+sid]=pg.evaluate(OVERFLOW)
        pg.evaluate("document.getElementById('owner').classList.add('hidden');document.getElementById('customer').classList.remove('hidden');window.role='customer'")
        for sid in cids:
            try: pg.evaluate(f"customerGo('{sid}')")
            except Exception as e: errs.append(f'customerGo({sid}) threw: {str(e)[:80]}')
            pg.wait_for_timeout(120); res['customer:'+sid]=pg.evaluate(OVERFLOW)
        bad={k:v for k,v in res.items() if v['docOverflow']>1 or v['items']}
        print(f'\n=== {w}px: {len(res)} screens | runtime errors: {len(errs)} | screens with overflow: {len(bad)}')
        for e in sorted(set(errs))[:6]: print('   ERR', e)
        for k,v in list(bad.items())[:8]: print('   OVF', k, v)
        pg.close()
    b.close()
