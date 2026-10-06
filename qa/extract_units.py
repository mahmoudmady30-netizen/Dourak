"""Extracts the pure business-logic functions from index.html into
qa/.units.generated.js so qa/unit_tests.js can test them in Node."""
import re, pathlib
root = pathlib.Path(__file__).resolve().parent
h = (root.parent / 'index.html').read_text(encoding='utf-8')
def extract(name):
    m = re.search(r'\n\s*(?:const|function)\s+%s\b' % name, h)
    if h[m.start():m.start()+40].strip().startswith('const'):
        return h[m.start():h.index(';\n', m.start())+1]
    i = h.index('{', m.start()); d = 0
    for j in range(i, len(h)):
        d += (h[j] == '{') - (h[j] == '}')
        if d == 0: return h[m.start():j+1]
names = ['validHour','normalizeHours','isWithinOpeningHours','isPastLastTokenTime','normalizePhone','BLOCKED_WORDS','normBad','BLOCKED_SET','BLOCKED_PHRASES','containsInappropriateLanguage']
(root / '.units.generated.js').write_text('\n'.join(extract(n) for n in names) + '\nmodule.exports={normalizeHours,isWithinOpeningHours,isPastLastTokenTime,normalizePhone,containsInappropriateLanguage};', encoding='utf-8')
print('extracted', len(names), 'units')
