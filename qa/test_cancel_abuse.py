import pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(__file__).resolve().parent; APP_URL = ROOT.parent.joinpath('index.html').as_uri()
MOCK = ROOT.joinpath('mock_firestore.js').read_text(encoding='utf-8'); res = []
def check(name, ok, detail=''): res.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.add_init_script("localStorage.setItem('dourakBusinessId','b1'); localStorage.setItem('tbCustomerProfile', JSON.stringify({name:'محمود',governorate:'دبي',phone:'0501234567'}));")
    pg.goto(APP_URL); pg.wait_for_timeout(700); pg.evaluate("document.getElementById('splash')?.remove()"); pg.evaluate(MOCK)
    ev = lambda js: pg.evaluate("(async()=>{" + js + "})()")
    ev("__db['businesses/b1']={name:'صالون',ownerId:'own1',active:true,confirmationMode:'auto',hours:'00:00 - 23:59'}; __db['businesses/b1/services/s1']={name:'قص',duration:30,price:40,active:true}; window.__who.uid='cust1';")
    join = lambda: ev("try{ return (await issueDourakTicket('b1','s1','قص')).id; }catch(e){ return 'ERR:'+(e.code||e.message); }")
    cancel = lambda tid: ev(f"try{{ await cancelDourakTicket('{tid}','x','b1'); return 'ok'; }}catch(e){{ return 'ERR:'+(e.code||e.message); }}")
    stats = lambda: pg.evaluate("__db['businesses/b1/customerStats/cust1']||null")
    # --- warnings shown before cancelling ---
    for c, cls in [(0, 'info'), (1, 'warn'), (2, 'danger')]:
        ev(f"dourakShowCancelConfirm('t', {{cancels:{c},left:{3-c},blocked:false}})")
        got = pg.evaluate("document.querySelector('#sheet .cancel-warn')?.className||''")
        check(f'confirm sheet before cancellation #{c+1} shows "{cls}" warning', cls in got, pg.evaluate("document.querySelector('#sheet .cancel-warn')?.textContent||''")[:70])
    ev("closeModal()")
    # --- attack: cancel without counting ---
    t1 = join()
    r = ev(f"try{{ await window.dourakFB.db.collection('businesses').doc('b1').collection('queueTickets').doc('{t1}').update({{status:'cancelled',cancelledAt:1,cancellationReason:'x'}}); return 'ALLOWED'; }}catch(e){{ return e.code; }}")
    check('ATTACK: cancel directly without counting it', r == 'permission-denied', r)
    # --- 3 normal cancellations ---
    check('cancellation #1 allowed', cancel(t1) == 'ok' and stats()['cancels'] == 1, str(stats() and stats()['cancels']))
    r = ev("try{ await window.dourakFB.db.collection('businesses').doc('b1').collection('customerStats').doc('cust1').set({cancels:0,windowStart:firebase.firestore.FieldValue.serverTimestamp(),lastCancelledTicketId:'zz'}); return 'ALLOWED'; }catch(e){ return e.code; }")
    check('ATTACK: reset own counter to 0', r == 'permission-denied', r)
    t2 = join(); check('cancellation #2 allowed', cancel(t2) == 'ok' and stats()['cancels'] == 2)
    t3 = join(); check('cancellation #3 allowed', cancel(t3) == 'ok' and stats()['cancels'] == 3)
    # --- lockout ---
    st = ev("return await dourakCancelState('b1')")
    check('after 3 cancellations the customer is blocked here', st['blocked'] is True and st['left'] == 0)
    r = join(); check('4th turn at the same place is refused by the rules', r.startswith('ERR:permission-denied'), r)
    ev("const s=await dourakCancelState('b1'); dourakShowCancelBlocked(s.until)")
    check('blocked sheet tells the customer when they can book again', 'تقدر تاخد دور تاني' in pg.evaluate("document.getElementById('sheet').textContent"))
    ev("closeModal(); __db['businesses/b2']={name:'مكان تاني',ownerId:'own2',active:true,confirmationMode:'auto',hours:'00:00 - 23:59'}; __db['businesses/b2/services/s1']={name:'x',duration:10,price:0,active:true};")
    r = ev("try{ return (await issueDourakTicket('b2','s1','x')).id; }catch(e){ return 'ERR:'+(e.code||e.message); }")
    check('other places are NOT affected by the block', not r.startswith('ERR'), r)
    # --- owner actions never count against the customer ---
    ev("__db['businesses/b1/queueTickets/r1']={customerId:'cust7',businessId:'b1',status:'pending_approval',number:50}; window.__who.uid='own1';")
    r = ev("try{ await window.dourakFB.db.collection('businesses').doc('b1').collection('queueTickets').doc('r1').update({status:'cancelled'}); return 'ok'; }catch(e){ return e.code; }")
    check("owner reject/cancel doesn't count against the customer", r == 'ok' and pg.evaluate("__db['businesses/b1/customerStats/cust7']") is None)
    # --- window expiry: 24h later the customer may book again; next cancel starts a new window ---
    ev("window.__who.uid='cust1'; __db['businesses/b1/customerStats/cust1'].windowStart=__mkTs(Date.now()-25*3600*1000);")
    st = ev("return await dourakCancelState('b1')"); check('after 24h the block lifts automatically', st['blocked'] is False and st['left'] == 3)
    t5 = join(); check('customer can take a turn again after 24h', not t5.startswith('ERR'), t5)
    check('next cancellation starts a fresh window (count = 1)', cancel(t5) == 'ok' and stats()['cancels'] == 1)
    b.close()
print(f"\nCANCEL-ABUSE RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
