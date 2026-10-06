# What the app writes must match what the V107 rules require, or real users
# would get "permission denied". A recording Firestore mock captures every
# write in each security-relevant flow.
import pathlib, json
from playwright.sync_api import sync_playwright
APP = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
res = []
def check(name, ok, detail=''):
    res.append(bool(ok)); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{str(detail)[:220]}]' if detail and not ok else ''))

MOCK = r"""
(() => {
  window.__writes = []; window.__docs = window.__docs || {};
  const D = window.__docs;
  const uid = localStorage.getItem('__uid') || 'owner1';
  const user = { uid, email: 'o@x.com', isAnonymous: false, emailVerified: true, providerData: [{ providerId: 'password' }] };
  const auth = { get currentUser() { return user; }, onAuthStateChanged(cb) { setTimeout(() => cb(user), 5); return () => {}; },
    setPersistence: () => Promise.resolve(), signInAnonymously: async () => ({ user }), getRedirectResult: async () => ({ user: null }), signOut: async () => {} };
  const kids = (p) => Object.keys(D).filter((k) => k.startsWith(p + '/') && !k.slice(p.length + 1).includes('/'));
  const snap = (k) => ({ id: k.split('/').pop(), exists: !!D[k], data: () => D[k], ref: ref(k) });
  const rec = (op, path, data, opts) => window.__writes.push({ op, path, data: JSON.parse(JSON.stringify(data || {}, (key, v) => (v && v.__fv) ? '<' + v.__fv + '>' : v)), merge: !!(opts && opts.merge) });
  const apply = (path, data, merge) => {
    const base = merge ? Object.assign({}, D[path] || {}) : {};
    Object.entries(data || {}).forEach(([k, v]) => { if (v && v.__fv === 'delete') delete base[k]; else if (!(v && v.__fv)) base[k] = JSON.parse(JSON.stringify(v)); });
    D[path] = base;
  };
  function q(path, f) {
    const rows = () => kids(path).filter((k) => f.every(([a, op, v]) => op === '==' ? D[k][a] === v : op === 'in' ? v.includes(D[k][a]) : true)).map(snap);
    return { where: (a, op, v) => q(path, [...f, [a, op, v]]), orderBy() { return this; }, limit() { return this; },
      get: async () => { const d = rows(); return { empty: !d.length, size: d.length, docs: d, forEach: (fn) => d.forEach(fn) }; },
      onSnapshot(cb) { setTimeout(() => { const d = rows(); cb({ empty: !d.length, size: d.length, docs: d, forEach: (fn) => d.forEach(fn), docChanges: () => [] }); }, 5); return () => {}; } };
  }
  function ref(path) { return { id: path.split('/').pop(), path,
    get: async () => snap(path), set: async (d, o) => { rec('set', path, d, o); apply(path, d, o && o.merge); },
    update: async (d) => { rec('update', path, d); apply(path, d, true); }, delete: async () => { rec('delete', path); delete D[path]; },
    collection: (n) => col(path + '/' + n), onSnapshot(cb) { setTimeout(() => cb(snap(path)), 5); return () => {}; } }; }
  let auto = 0;
  function col(path) { return Object.assign(q(path, []), { doc: (id) => ref(path + '/' + (id || 'auto' + (++auto))), add: async (d) => { const r = ref(path + '/auto' + (++auto)); rec('add', r.path, d); apply(r.path, d); return r; } }); }
  const batchObj = () => { const ops = []; return { set(r, d, o) { ops.push(() => r.set(d, o)); }, update(r, d) { ops.push(() => r.update(d)); }, delete(r) { ops.push(() => r.delete()); }, commit: async () => { window.__writes.push({ op: 'batch-begin' }); for (const o of ops) await o(); window.__writes.push({ op: 'batch-end' }); } }; };
  const fs = () => ({ collection: (n) => col(n), batch: batchObj,
    runTransaction: async (fn) => { const b = batchObj(); await fn({ get: (r) => r.get(), set: (r, d, o) => b.set(r, d, o), update: (r, d) => b.update(r, d), delete: (r) => b.delete(r) }); await b.commit(); } });
  fs.FieldValue = { serverTimestamp: () => ({ __fv: 'serverTimestamp' }), delete: () => ({ __fv: 'delete' }), increment: (n) => ({ __fv: 'increment' + n }), arrayUnion: () => ({ __fv: 'arrayUnion' }) };
  const a = () => auth; a.Auth = { Persistence: { LOCAL: 'local' } }; a.GoogleAuthProvider = function () { this.setCustomParameters = () => {}; }; a.EmailAuthProvider = { credential: () => ({}) };
  Object.defineProperty(window, 'firebase', { value: { initializeApp: () => ({}), auth: a, firestore: fs, apps: [] }, writable: false });
})();
"""

def page(p, uid, role, docs, extra=''):
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 390, 'height': 844}); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:160])); pg.on('dialog', lambda d: d.accept())
    seed = f"""localStorage.setItem('__uid','{uid}'); window.__docs = {json.dumps(docs)};
      localStorage.setItem('tbUser', JSON.stringify({{uid:'{uid}',role:'{role}',email:'o@x.com',provider:'password'}}));
      localStorage.setItem('dourakLastRole','{role}'); localStorage.setItem('dourakLastRoleUid','{uid}');
      localStorage.setItem('tbCustomerProfile', JSON.stringify({{name:'م',governorate:'دبي',phone:'0501234567'}})); {extra}"""
    pg.add_init_script(seed + MOCK); pg.goto(APP); pg.wait_for_timeout(1500)
    pg.evaluate("document.getElementById('splash')?.remove()")
    return b, pg, errs

BIZ = {'businesses/b1': {'name': 'صالون', 'ownerId': 'owner1', 'active': True, 'hours': '00:00 - 23:59', 'confirmationMode': 'auto', 'businessCode': 'DRK-ABC1234'},
       'businesses/b1/services/s1': {'name': 'قص', 'duration': 30, 'price': 40, 'active': True},
       'businesses/b1/queue/current': {'nextNumber': 5, 'currentNumber': 2, 'waitingCount': 1, 'servedCount': 1}}

with sync_playwright() as p:
    # ---- owner: create a staff member
    docs = dict(BIZ); docs['businesses/b1/staff/old1'] = {'name': 'قديم', 'role': 'employee', 'active': True, 'username': 'old1234', 'passcode': '1234'}
    docs['staffLogins/old1234'] = {'businessId': 'b1', 'staffId': 'old1', 'name': 'قديم', 'passcode': '1234'}
    b, pg, errs = page(p, 'owner1', 'owner', docs, "localStorage.setItem('dourakBusinessId','b1'); localStorage.setItem('tbSetup', JSON.stringify({businessId:'b1',name:'صالون',ownerId:'owner1'}));")
    pg.evaluate("ownerGo('oStaff')"); pg.wait_for_timeout(800)
    D = pg.evaluate("window.__docs")
    check('legacy passcode moved into the owner-only store', D.get('businesses/b1/staffSecrets/old1', {}).get('passcode') == '1234', D.get('businesses/b1/staffSecrets/old1'))
    check('legacy passcode removed from the public staff record', 'passcode' not in D.get('businesses/b1/staff/old1', {}), D.get('businesses/b1/staff/old1'))
    check('legacy passcode removed from the public login lookup', 'passcode' not in D.get('staffLogins/old1234', {}), D.get('staffLogins/old1234'))
    pg.evaluate("window.__writes=[]; openStaffEditor(''); document.getElementById('staffEditName').value='Sara';")
    pg.evaluate("saveStaff('')"); pg.wait_for_timeout(700)
    W = pg.evaluate("window.__writes")
    staff_w = [w for w in W if w.get('path', '').startswith('businesses/b1/staff/') and w['op'] == 'set']
    login_w = [w for w in W if w.get('path', '').startswith('staffLogins/') and w['op'] == 'set']
    secret_w = [w for w in W if w.get('path', '').startswith('businesses/b1/staffSecrets/') and w['op'] == 'set']
    check('new staff: public record carries no passcode', staff_w and 'passcode' not in staff_w[0]['data'], staff_w)
    check('new staff: login lookup carries no passcode', login_w and set(login_w[0]['data']) <= {'businessId', 'staffId', 'name'}, login_w)
    check('new staff: passcode stored in owner-only staffSecrets, 6 digits', secret_w and len(secret_w[0]['data'].get('passcode', '')) == 6 and secret_w[0]['data']['passcode'].isdigit(), secret_w)
    check('new staff: shown to the owner once in the credentials sheet', secret_w and secret_w[0]['data']['passcode'] in pg.evaluate("document.getElementById('sheet').textContent"))
    new_id = secret_w[0]['path'].split('/')[-1] if secret_w else ''
    pg.evaluate("closeModal()"); pg.evaluate("window.__writes=[]")
    pg.evaluate(f"deleteStaff('{new_id}', 0)"); pg.wait_for_timeout(500)
    W = pg.evaluate("window.__writes")
    check('deleting staff removes their secret', any(w['op'] == 'delete' and w.get('path') == f'businesses/b1/staffSecrets/{new_id}' for w in W), W)
    check('no page errors (owner staff flows)', not errs, errs); b.close()

    # ---- staff login writes: counted attempt, then verified session
    docs = dict(BIZ); docs['staffLogins/sara1234'] = {'businessId': 'b1', 'staffId': 'st1', 'name': 'Sara'}
    docs['businesses/b1/staff/st1'] = {'name': 'Sara', 'active': True, 'username': 'sara1234'}
    b, pg, errs = page(p, 'anonStaff', 'customer', docs)
    pg.evaluate("document.getElementById('staffUsernameInput').value='sara1234'; document.getElementById('staffPasscodeInput').value='123456'; window.__writes=[];")
    pg.evaluate("staffLogin()"); pg.wait_for_timeout(800)
    W = [w for w in pg.evaluate("window.__writes") if w.get('path')]
    paths = [w['path'] for w in W]
    att = next((w for w in W if w['path'] == 'businesses/b1/staffAuth/st1'), None)
    check('staff login first records an attempt (uid + guess + counted try)', att and att['data'].get('uid') == 'anonStaff' and att['data'].get('guess') == '123456' and str(att['data'].get('tries')).startswith('<increment'), att)
    ses = next((w for w in W if w['path'] == 'businesses/b1/staffSessions/anonStaff'), None)
    check('then requests a staff session holding only staffId + time', ses and set(ses['data']) == {'staffId', 'createdAt'} and ses['data']['staffId'] == 'st1', ses)
    check('attempt is written before the session', 'businesses/b1/staffAuth/st1' in paths and paths.index('businesses/b1/staffAuth/st1') < paths.index('businesses/b1/staffSessions/anonStaff'), paths)
    check('staff login never reads or sends a stored passcode', not any('passcode' in w['data'] for w in W), W)
    check('no page errors (staff login)', not errs, errs); b.close()

    # ---- customer joins the queue: counter change names its ticket
    b, pg, errs = page(p, 'cust1', 'customer', dict(BIZ))
    pg.evaluate("window.__writes=[]"); pg.evaluate("issueDourakTicket('b1','s1','قص')"); pg.wait_for_timeout(600)
    W = pg.evaluate("window.__writes")
    qw = next((w for w in W if w.get('path') == 'businesses/b1/queue/current'), None)
    tw = next((w for w in W if w.get('path', '').startswith('businesses/b1/queueTickets/')), None)
    check('join: counter write names the ticket issued in the same transaction', qw and tw and qw['data'].get('lastIssuedTicketId') == tw['path'].split('/')[-1], (qw, tw and tw['path']))
    check('join: ticket number equals the counter before the join', tw and tw['data'].get('number') == 5, tw)
    check('join: ticket status follows the owner confirmation mode (auto -> waiting)', tw and tw['data'].get('status') == 'waiting', tw)
    check('no page errors (join)', not errs, errs); b.close()

    # ---- admin: never self-granted
    b, pg, errs = page(p, 'someone', 'admin', dict(BIZ))
    pg.wait_for_timeout(800)
    W = pg.evaluate("window.__writes")
    check('admin login does NOT write an admin role anywhere', not any(w.get('data', {}).get('role') == 'admin' for w in W), W)
    check('non-admin account sees "not an admin" with its account ID to add in the Console', 'someone' in pg.evaluate("document.getElementById('adminBusinessList')?.textContent || ''"))
    b.close()

    # ---- new business: created together with its code registry entry
    b, pg, errs = page(p, 'owner1', 'owner', {})
    check('link opener refuses non-web schemes', pg.evaluate("dourakSafeExternalUrl('java'+'script:alert(1)')") == '' and pg.evaluate("dourakSafeExternalUrl('https://wa.me/971')") == 'https://wa.me/971')
    b.close()

print(f"\nSECURITY-WRITE-SHAPES RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
