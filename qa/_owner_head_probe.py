import pathlib, io, json, sys
from collections import Counter
from playwright.sync_api import sync_playwright
from PIL import Image
APP_URL = pathlib.Path('/home/claude/work/dourak_v23/index.html').as_uri()

FILL = """
document.getElementById('splash')?.remove();
document.getElementById('auth').classList.add('hidden');
document.getElementById('owner').classList.remove('hidden');
document.body.classList.remove('theme-classic','theme-apple');
document.body.classList.add('theme-%s');
document.getElementById('oHome').classList.add('active');
document.getElementById('ownerName').textContent='هيلبو';
document.getElementById('ownerAddress').textContent='كوبا · 📞 0527091779';
document.getElementById('ownerBusinessCodeCard').classList.remove('hidden');
document.getElementById('ownerBusinessCode').textContent='DRK-82Y4987';
const b=document.getElementById('ownerOpenBadge'); b.className='badge open'; b.textContent='● مفتوح';
document.getElementById('ownerHoursNow').textContent='24/7';
document.getElementById('owWaiting').textContent='0';
document.getElementById('owCurrent').textContent='A009';
document.getElementById('owServed').textContent='9';
document.querySelector('.callnext-btn').disabled = true;
"""

def lum(c):
    c = [v/255 for v in c]
    c = [v/12.92 if v <= .03928 else ((v+.055)/1.055)**2.4 for v in c]
    return .2126*c[0]+.7152*c[1]+.0722*c[2]
def ratio(a,b):
    la, lb = lum(a), lum(b); hi, lo = max(la,lb), min(la,lb)
    return (hi+.05)/(lo+.05)

def probe(theme, shot=None):
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={'width':390,'height':700})
        pg.goto(APP_URL); pg.wait_for_timeout(500)
        pg.evaluate(FILL % theme); pg.wait_for_timeout(300)
        if shot: pg.screenshot(path=shot, clip={'x':0,'y':0,'width':390,'height':560})
        targets = {
          'business name': '#ownerName', 'address': '#ownerAddress',
          'code label': '#ownerBusinessCodeCard span', 'code value': '#ownerBusinessCode',
          'code hint': '#ownerBusinessCodeCard small', 'hours': '#ownerHoursNow',
          'open badge': '#ownerOpenBadge', 'stat number': '#owCurrent',
          'stat label': '.owner-stat small', 'call next': '.callnext-btn', 'walk-in': '.walkin-btn',
        }
        out = {}
        for name, sel in targets.items():
            el = pg.locator(sel).first
            box = el.bounding_box()
            if not box or box['width'] < 2: out[name] = None; continue
            png = pg.screenshot(clip=box)
            im = Image.open(io.BytesIO(png)).convert('RGB')
            px = list(im.getdata())
            bg = Counter(px).most_common(1)[0][0]
            # text colour = the pixel farthest from the background (a real glyph stroke)
            fg = max(px, key=lambda q: sum(abs(q[i]-bg[i]) for i in range(3)))
            out[name] = round(ratio(fg, bg), 2)
        br.close(); return out

if __name__ == '__main__':
    theme = sys.argv[1]
    print(json.dumps(probe(theme, f'/home/claude/shots/raw/probe_{theme}.png'), ensure_ascii=False, indent=1))
