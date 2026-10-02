# Every text element in the owner header, measured from real rendered pixels
# (WCAG contrast ratio, glyph colour vs. its own background), across both
# themes x light/dark mode x call-next enabled/disabled. Replaces the earlier
# per-element theme tests: those only checked the elements someone had
# already noticed, which is exactly how the rest stayed broken.
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import _owner_head_probe as P
from playwright.sync_api import sync_playwright
import io
from collections import Counter
from PIL import Image
res = []
def check(name, ok, detail=''):
    res.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

def run(theme, dark, enabled):
    fill = P.FILL % theme
    if dark: fill += "document.body.classList.add('dark');"
    if enabled: fill += "document.querySelector('.callnext-btn').disabled=false; document.querySelector('.callnext-btn').classList.remove('btn-disabled');"
    with sync_playwright() as p:
        br = p.chromium.launch(); pg = br.new_page(viewport={'width':390,'height':700}); errs=[]
        pg.on('pageerror', lambda e: errs.append(str(e)[:120]))
        pg.goto(P.APP_URL); pg.wait_for_timeout(500); pg.evaluate(fill); pg.wait_for_timeout(300)
        sels = {'business name':'#ownerName','address':'#ownerAddress','code label':'#ownerBusinessCodeCard span',
                'code value':'#ownerBusinessCode','code hint':'#ownerBusinessCodeCard small','hours':'#ownerHoursNow',
                'open badge':'#ownerOpenBadge','stat number':'#owCurrent','stat label':'.owner-stat small',
                'call next':'.callnext-btn','walk-in':'.walkin-btn'}
        out = {}
        for n, s in sels.items():
            box = pg.locator(s).first.bounding_box()
            im = Image.open(io.BytesIO(pg.screenshot(clip=box))).convert('RGB'); px = list(im.getdata())
            bg = Counter(px).most_common(1)[0][0]
            fg = max(px, key=lambda q: sum(abs(q[i]-bg[i]) for i in range(3)))
            out[n] = round(P.ratio(fg, bg), 2)
        br.close(); return out, errs

for theme, label in (('apple','كلاسيك'), ('classic','أساسي')):
    for dark in (False, True):
        for enabled in (False, True):
            r, errs = run(theme, dark, enabled)
            worst = min(r, key=r.get)
            tag = f"{label} / {'dark' if dark else 'light'} / call-next {'enabled' if enabled else 'disabled'}"
            check(f'{tag}: all 11 header elements >= 4.5:1', r[worst] >= 4.5, f'worst={worst} {r[worst]}')
            if errs: check(f'{tag}: no page errors', False, str(errs))

print(f"\nOWNER-HEADER-CONTRAST RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
