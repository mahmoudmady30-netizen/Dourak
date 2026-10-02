# App-wide readability scanner: every visible text element on every screen,
# glyph colour vs. its own background, measured from rendered pixels.
import pathlib, io, json, sys
from collections import Counter
from PIL import Image
from playwright.sync_api import sync_playwright
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()

def _lin(v):
    v/=255; return v/12.92 if v<=.03928 else ((v+.055)/1.055)**2.4
def lum(c): return .2126*_lin(c[0])+.7152*_lin(c[1])+.0722*_lin(c[2])
def ratio(a,b):
    x,y=lum(a),lum(b); return (max(x,y)+.05)/(min(x,y)+.05)

TEXT_ELS = r"""(skipAuth) => {
  const out=[]; const vw=innerWidth, vh=innerHeight;
  document.querySelectorAll('body *').forEach(el=>{
    if (el.closest('.hidden') || el.closest('#splash')) return;
    if (skipAuth && el.closest('#auth')) return;
    const direct=[...el.childNodes].some(n=>n.nodeType===3 && n.textContent.trim().length>0);
    if(!direct) return;
    const cs=getComputedStyle(el);
    if(cs.display==='none'||cs.visibility==='hidden'||+cs.opacity===0) return;
    // Emoji-only labels (icons) carry their own colours — not text contrast.
    const txt=[...el.childNodes].filter(n=>n.nodeType===3).map(n=>n.textContent).join('').trim();
    if(!/[\u0600-\u06FFA-Za-z0-9]/.test(txt)) return;
    const r=el.getBoundingClientRect();
    if(r.width<6||r.height<6||r.bottom<0||r.top>vh||r.right<0||r.left>vw) return;
    if(el.tagName==='INPUT'||el.tagName==='TEXTAREA'||el.tagName==='SELECT'||el.tagName==='OPTION') return;
    const id=el.id?'#'+el.id:el.tagName.toLowerCase()+(el.classList.length?'.'+[...el.classList].slice(0,2).join('.'):'');
    let s=el, surf='(page)'; while(s&&s!==document.body){ const c=getComputedStyle(s); if((c.backgroundColor&&c.backgroundColor!=='rgba(0, 0, 0, 0)')||c.backgroundImage!=='none'){ surf=s.id?'#'+s.id:s.tagName.toLowerCase()+(s.classList.length?'.'+[...s.classList].slice(0,2).join('.'):''); break;} s=s.parentElement; }
    out.push({id, surf, col:cs.color, txt:txt.slice(0,28), x:Math.max(0,r.left), y:Math.max(0,r.top), w:Math.min(r.width,vw-Math.max(0,r.left)), h:Math.min(r.height,vh-Math.max(0,r.top))});
  });
  return out;
}"""

def measure(pg, skip_auth=False):
    full=Image.open(io.BytesIO(pg.screenshot())).convert('RGB')
    rows=[]
    for e in pg.evaluate(TEXT_ELS, skip_auth):
        ins=3 if min(e['w'],e['h'])>14 else 0  # skip rounded-corner slivers of whatever sits behind
        box=(int(e['x'])+ins,int(e['y'])+ins,int(e['x']+e['w'])-ins,int(e['y']+e['h'])-ins)
        if box[2]-box[0]<4 or box[3]-box[1]<4: continue
        px=list(full.crop(box).getdata())
        bg=Counter(px).most_common(1)[0][0]
        _n=[float(v) for v in __import__('re').findall(r'[\d.]+', e['col'])]
        if len(_n)>=3:
            _fg=tuple(int(v) for v in _n[:3])
            # background = most common pixel that is NOT the text colour (big
            # bold glyphs can cover most of their own box)
            # sample the background from the box's edge ring (glyphs and
            # emoji sit in the middle; the background always touches edges)
            _c=full.crop(box); _w,_h=_c.size; _ring=[]
            for _x in range(_w): _ring+= [_c.getpixel((_x,0)), _c.getpixel((_x,_h-1))]
            for _y in range(_h): _ring+= [_c.getpixel((0,_y)), _c.getpixel((_w-1,_y))]
            _rest=[q for q in _ring if sum(abs(q[i]-_fg[i]) for i in range(3))>60] or [q for q in px if sum(abs(q[i]-_fg[i]) for i in range(3))>60]
            if _rest: bg=Counter(_rest).most_common(1)[0][0]
        import re as _re
        nums=[float(v) for v in _re.findall(r'[\d.]+', e['col'])]
        if len(nums)==3 or (len(nums)==4 and nums[3]>=0.99): fg=tuple(int(v) for v in nums[:3])
        else: fg=max(px,key=lambda q:sum(abs(q[i]-bg[i]) for i in range(3)))
        rows.append((round(ratio(fg,bg),2), e['id'], e['txt'], e['surf']))
    return rows

SEED = """localStorage.setItem('tbSetup', JSON.stringify({businessId:'b1',name:'هيلبو',address:'كوبا',hours:'00:00 - 23:59'}));
localStorage.setItem('dourakBusinessId','b1');"""

def scan(preset, dark, width=390, shots_dir=None):
    init = SEED + f"localStorage.setItem('tbTheme','{'dark' if dark else 'light'}');localStorage.setItem('tbThemePresetOwner','{preset}');localStorage.setItem('tbThemePresetCustomer','{preset}');"
    report={}
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={'width':width,'height':844}); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)[:120]))
        pg.add_init_script(init); pg.goto(APP_URL); pg.wait_for_timeout(700)
        pg.evaluate("document.getElementById('splash')?.remove()")
        # Measure settled colours, not mid-transition frames.
        pg.add_style_tag(content="*,*::before,*::after{transition:none!important;animation:none!important}")
        def shot(name):
            if shots_dir: pg.screenshot(path=f'{shots_dir}/{preset}_{"dark" if dark else "light"}_{name.replace(":","_")}.png')
        # auth
        pg.evaluate("['owner','customer'].forEach(i=>document.getElementById(i).classList.add('hidden'));document.getElementById('auth').classList.remove('hidden');showAuthLanding()")
        pg.wait_for_timeout(150); report['auth-landing']=measure(pg); shot('auth-landing')
        pg.evaluate("showAuthLogin('customer')"); pg.wait_for_timeout(150); report['auth-login']=measure(pg); shot('auth-login')
        # owner
        pg.evaluate("document.getElementById('auth').classList.add('hidden');document.getElementById('owner').classList.remove('hidden');window.role='owner'")
        for sid in pg.evaluate("[...document.querySelectorAll('#owner .screen')].map(s=>s.id)"):
            pg.evaluate("document.getElementById('auth').classList.add('hidden');document.querySelector('.toast')?.classList.remove('show')")
            try: pg.evaluate(f"ownerGo('{sid}')")
            except Exception: pass
            pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(120)
            pg.evaluate("document.getElementById('auth').classList.add('hidden')")
            report['owner:'+sid]=measure(pg, True); shot('owner:'+sid)
        # customer
        pg.evaluate("document.getElementById('owner').classList.add('hidden');document.getElementById('customer').classList.remove('hidden');window.role='customer'")
        for sid in pg.evaluate("[...document.querySelectorAll('#customer .screen')].map(s=>s.id)"):
            pg.evaluate("document.getElementById('auth').classList.add('hidden')")
            try: pg.evaluate(f"customerGo('{sid}')")
            except Exception: pass
            pg.evaluate("window.scrollTo(0,0)"); pg.wait_for_timeout(120)
            pg.evaluate("document.getElementById('auth').classList.add('hidden')")
            report['customer:'+sid]=measure(pg, True); shot('customer:'+sid)
        b.close()
    return report, errs

if __name__=='__main__':
    preset, mode = sys.argv[1], sys.argv[2]
    rep, errs = scan(preset, mode=='dark', shots_dir='/home/claude/shots/scan')
    total=sum(len(v) for v in rep.values()); bad=[(s,r) for s,rows in rep.items() for r in rows if r[0]<3.0]
    weak=[(s,r) for s,rows in rep.items() for r in rows if 3.0<=r[0]<4.5]
    if '-w' in sys.argv:
        for s,r in sorted(weak, key=lambda x:x[1][0]): print('  WEAK', r[0], s, r[1], '|', r[2], '| on', r[3])
    print(f'{preset}/{mode}: {len(rep)} screens, {total} text elements | unreadable(<3): {len(bad)} | weak(3-4.5): {len(weak)} | errors: {len(errs)}')
    from collections import Counter as C
    print('  failing texts by SURFACE behind them:')
    for k,v in C(r[3] for s,r in bad).most_common(25): print(f'   {v:3d}  {k}')
    if '-v' in sys.argv:
        for s,r in sorted(bad, key=lambda x:x[1][0]): print('  BAD ', r[0], s, r[1], '|', r[2], '| on', r[3])
