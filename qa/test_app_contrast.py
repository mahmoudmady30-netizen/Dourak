# App-wide readability: every visible text element on all 18 screens, in all
# 4 theme combinations, measured from rendered pixels (WCAG contrast).
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import _contrast_scan as S
res=[]
for preset, label in (('apple','كلاسيك'),('classic','أساسي')):
    for dark in (False, True):
        rep, errs = S.scan(preset, dark)
        rows=[(s,r) for s,rr in rep.items() for r in rr]
        bad=[x for x in rows if x[1][0] < 4.5]
        ok = not bad and not errs
        res.append(ok)
        tag=f"{label} / {'dark' if dark else 'light'}"
        print(('PASS ' if ok else 'FAIL ') + f"{tag}: {len(rep)} screens, {len(rows)} text elements, all >= 4.5:1" + (f"  [{len(bad)} below: {bad[:3]}]" if bad else '') + (f"  [errors: {errs[:2]}]" if errs else ''))
print(f"\nAPP-CONTRAST RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
