# "دوري" badge must clear when the customer's turn ends — including the exact
# conditions that used to leave it stuck: the places list not loaded yet at
# start-up, a ticket at a place NOT in that list, and a stale ticket saved in
# the phone's storage from a previous session.
import pathlib, json
from playwright.sync_api import sync_playwright
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
res = []
def check(name, ok, detail=''):
    res.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))

MOCK = r"""
(() => {
  // server state: tickets per business; live listeners re-fire on change
  window.__srv = { b9: { t1: { customerId:'cust1', businessId:'b9', businessName:'صالون بعيد', status:'waiting', number:7, type:'queue' } },
                   b3: { tOld: { customerId:'cust1', businessId:'b3', businessName:'قديم', status:'served', number:2, type:'queue' } } };
  const listeners = [];
  window.__emit = () => listeners.forEach((l) => l.fire());
  window.__setStatus = (bid, id, st) => { window.__srv[bid][id].status = st; window.__emit(); };
  window.__listenerBids = () => [...new Set(listeners.filter(l => l.kind==='tickets').map(l => l.bid))];
  const user = { uid:'cust1', email:'c@x.com', isAnonymous:false, providerData:[{providerId:'password'}] };
  const auth = { get currentUser(){return user;}, onAuthStateChanged(cb){ setTimeout(()=>cb(user),10); return ()=>{}; },
    setPersistence:()=>Promise.resolve(), signInAnonymously: async()=>({user}), getRedirectResult: async()=>({user:null}), signOut: async()=>{} };
  const snapOf = (docs) => ({ empty: !docs.length, docs: docs.map(([id,d]) => ({ id, data:()=>d, exists:true })) });
  function query(path, filters) {
    return {
      where(f, op, v){ return query(path, [...filters, [f,op,v]]); }, orderBy(){ return this; }, limit(){ return this; },
      _rows(){
        const m = /^businesses\/([^/]+)\/queueTickets$/.exec(path);
        if (!m) return [];
        return Object.entries(window.__srv[m[1]] || {}).filter(([id,d]) => filters.every(([f,op,v]) =>
          op==='==' ? d[f]===v : op==='in' ? v.includes(d[f]) : true));
      },
      get: async function(){ return snapOf(this._rows()); },
      onSnapshot(cb){
        const m = /^businesses\/([^/]+)\/queueTickets$/.exec(path);
        const l = { kind: m ? 'tickets' : 'other', bid: m ? m[1] : null, fire: () => cb(snapOf(this._rows())) };
        listeners.push(l); setTimeout(l.fire, 5); return () => { const i = listeners.indexOf(l); if (i>=0) listeners.splice(i,1); };
      }
    };
  }
  function doc(path){ return { path, get: async()=>({exists:false, data:()=>({})}), set: async()=>{}, update: async()=>{},
    collection:(n)=>col(path+'/'+n), onSnapshot(cb){ setTimeout(()=>cb({exists:false,data:()=>({})}),5); return ()=>{}; } }; }
  function col(path){ return Object.assign(query(path, []), { doc:(id)=>doc(path+'/'+(id||'auto')) }); }
  const fs = () => ({ collection:(n)=>col(n), runTransaction: async(fn)=>fn({get:async(r)=>r.get(),set(){},update(){}}) });
  fs.FieldValue = { serverTimestamp:()=>({}), delete:()=>({}), increment:()=>({}) };
  const a = () => auth; a.Auth = { Persistence:{ LOCAL:'local' } }; a.GoogleAuthProvider = function(){ this.setCustomParameters=()=>{}; };
  Object.defineProperty(window,'firebase',{value:{initializeApp:()=>({}),auth:a,firestore:fs,apps:[]},writable:false});
  // Signed-in customer who took a turn in an earlier session: the ticket at
  // b9 (still waiting on the server) AND a stale one at b3 that the server
  // already served while the phone was offline — both saved on the phone.
  localStorage.setItem('tbUser', JSON.stringify({uid:'cust1',role:'customer',email:'c@x.com',provider:'password'}));
  localStorage.setItem('tbCustomerProfile', JSON.stringify({name:'محمود',governorate:'دبي',phone:'0501234567'}));
  localStorage.setItem('dourakLastRole','customer'); localStorage.setItem('dourakLastRoleUid','cust1');
  localStorage.setItem('tbActiveTokens', JSON.stringify([
    {id:'t1', businessId:'b9', placeId:'b9', place:'صالون بعيد', number:'A007', status:'waiting', type:'queue'},
    {id:'tOld', businessId:'b3', placeId:'b3', place:'قديم', number:'A002', status:'waiting', type:'queue'}]));
})();
"""

BADGE = "(()=>{const b=document.getElementById('cQueueNavBadge'); return {shown: b.classList.contains('show'), text: b.textContent};})()"

with sync_playwright() as p:
    br = p.chromium.launch(); pg = br.new_page(viewport={'width':390,'height':844}); errs=[]
    pg.on('pageerror', lambda e: errs.append(str(e)[:160]))
    pg.add_init_script(MOCK); pg.goto(APP_URL); pg.wait_for_timeout(2500)

    bids = pg.evaluate("window.__listenerBids()")
    check('ticket listeners exist even though neither business is in the places list', 'b9' in bids and 'b3' in bids, str(bids))
    b = pg.evaluate(BADGE)
    check('stale ticket (already served while offline) is dropped on first server snapshot; badge shows only the real one', b['shown'] and b['text'] == '1', str(b))

    # the reported scenario: the turn ends
    pg.evaluate("window.__setStatus('b9','t1','called')"); pg.wait_for_timeout(300)
    b = pg.evaluate(BADGE)
    check('while being called the ticket still counts (turn not over yet)', b['shown'] and b['text'] == '1', str(b))
    pg.evaluate("window.__setStatus('b9','t1','served')"); pg.wait_for_timeout(400)
    b = pg.evaluate(BADGE)
    check('THE REPORTED BUG — after the turn is served, the دوري badge clears', not b['shown'], str(b))
    check('active tickets list is empty after serving', pg.evaluate("(window.activeTokens||[]).length") == 0 or pg.evaluate("JSON.parse(localStorage.tbActiveTokens||'[]').length") == 0)
    check('the cleared state is what gets saved on the phone (no ghost after restart)', pg.evaluate("JSON.parse(localStorage.tbActiveTokens||'[]').length") == 0, pg.evaluate("localStorage.tbActiveTokens"))

    # a NEW turn taken later, at a business never seen before — mirrors the
    # real join path: the ticket is added locally, then persistActiveTokens()
    # runs, which now re-syncs listeners.
    pg.evaluate("""window.__srv.b5 = { tNew: { customerId:'cust1', businessId:'b5', businessName:'جديد', status:'waiting', number:3, type:'queue' } };""")
    pg.evaluate("""window.activeTokens.push({id:'tNew',businessId:'b5',placeId:'b5',place:'جديد',number:'A003',status:'waiting',type:'queue'}); window.dourakSyncCustomerTicketListeners();""")
    pg.wait_for_timeout(400)
    check('a listener is attached for the new business immediately (no restart needed)', 'b5' in pg.evaluate("window.__listenerBids()"), str(pg.evaluate("window.__listenerBids()")))
    check('new turn shows the badge', pg.evaluate(BADGE)['shown'], str(pg.evaluate(BADGE)))
    pg.evaluate("window.__setStatus('b5','tNew','cancelled')"); pg.wait_for_timeout(400)
    check('a cancelled turn also clears the badge', not pg.evaluate(BADGE)['shown'], str(pg.evaluate(BADGE)))

    check('no page errors', not errs, str(errs[:3]))
    br.close()
print(f"\nQUEUE-BADGE RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
