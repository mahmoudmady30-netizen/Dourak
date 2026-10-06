// In-browser Firestore mock that ENFORCES the rule logic for queueTickets,
// otpSecrets and ticketContacts (mirrors firestore.rules), so the real app
// code can be exercised as owner / customer / attacker.
(() => {
  const DEL = { __del: 1 }; const TS = () => ({ __ts: 1, __now: 1, toMillis: () => Date.now() });
  const mk = (ms) => ({ __ts: 1, ms, toMillis() { return this.ms; } }); const isNow = (v) => !!(v && v.__now); const W = 24 * 3600 * 1000;
  const material = (o) => { const r = {}; for (const [k, v] of Object.entries(o)) r[k] = isNow(v) ? mk(Date.now()) : v; return r; };
  window.firebase = { firestore: { FieldValue: { delete: () => DEL, serverTimestamp: TS } } };
  const db = window.__db = {}; window.__who = { uid: 'cust1' }; const OWNER = 'own1';
  const denied = () => { const e = new Error('Missing or insufficient permissions.'); e.code = 'permission-denied'; throw e; };
  const TICKET_KEYS = ['customerId','serviceId','number','status','businessId','createdAt','businessName','serviceName','duration','price','walkIn','type','appointmentAt'];
  function rules(op, path, before, after) {
    const p = path.split('/'), sub = p[2], id = p[3], uid = window.__who.uid, owner = uid === OWNER;
    if (sub === 'customerStats') {
      if (op === 'read') { if (!owner && id !== uid) denied(); return; }
      if (owner) return; if (id !== uid) denied();
      if (Object.keys(after).some((k) => !['cancels','windowStart','lastCancelledTicketId'].includes(k))) denied();
      if (op === 'create') { if (after.cancels === 1 && isNow(after.windowStart) && typeof after.lastCancelledTicketId === 'string') return; denied(); }
      if (typeof after.lastCancelledTicketId !== 'string' || after.lastCancelledTicketId === before.lastCancelledTicketId) denied();
      const inWin = Date.now() <= before.windowStart.ms + W;
      if (inWin && after.windowStart?.ms === before.windowStart.ms && after.cancels === before.cancels + 1) return;
      if (!inWin && isNow(after.windowStart) && after.cancels === 1) return;
      denied();
    }
    if (sub === 'otpSecrets') { if (!owner) denied(); if (after && (Object.keys(after).some((k) => !['code','createdAt'].includes(k)) || String(after.code).length !== 6)) denied(); return; }
    if (sub === 'ticketContacts') {
      if (op === 'read') { if (!owner && before?.customerId !== uid) denied(); return; }
      if (after && Object.keys(after).some((k) => !['customerId','customerName','customerPhone','createdAt'].includes(k))) denied();
      if (owner) return; if (op === 'create' && after.customerId === uid && db[`businesses/${p[1]}/queueTickets/${id}`]?.customerId === uid) return; denied();
    }
    if (sub === 'queueTickets') {
      if (op === 'read') return;
      if (op === 'create') { if (after.customerId !== uid && !owner) denied(); if (Object.keys(after).some((k) => !TICKET_KEYS.includes(k))) denied(); const st = db[`businesses/${p[1]}/customerStats/${uid}`]; if (st && st.cancels >= 3 && Date.now() <= st.windowStart.ms + W) denied(); return; }
      if (owner) return; if (before.customerId !== uid) denied();
      const ch = [...new Set([...Object.keys(before), ...Object.keys(after)])].filter((k) => JSON.stringify(before[k]) !== JSON.stringify(after[k]));
      if (before.status === 'pending_otp' && ch.every((k) => ['otpAttempt','otpTries'].includes(k)) && typeof after.otpAttempt === 'string' && after.otpAttempt.length === 6 && after.otpTries === (before.otpTries || 0) + 1 && after.otpTries <= 5) return;
      if (before.status === 'pending_otp' && ch.length === 1 && ch[0] === 'status' && ((before.type === 'appointment' && after.status === 'scheduled') || (before.type !== 'appointment' && after.status === 'waiting'))) { const s = db[`businesses/${p[1]}/otpSecrets/${id}`]; if (s && (before.otpAttempt || '') === s.code) return; }
      if (ch.every((k) => ['status','cancelledAt','cancellationReason'].includes(k)) && after.status === 'cancelled' && db[`businesses/${p[1]}/customerStats/${uid}`]?.lastCancelledTicketId === id) return;
      denied();
    }
  }
  const apply = (base, data) => { const o = { ...(base || {}) }; for (const [k, v] of Object.entries(data)) { if (v === DEL) delete o[k]; else o[k] = v; } return o; };
  const snap = (path, d) => ({ id: path.split('/').pop(), exists: !!d, data: () => (d ? { ...d } : undefined) });
  function docRef(path) {
    return { id: path.split('/').pop(), path,
      collection: (n) => collRef(`${path}/${n}`),
      get: async () => { rules('read', path, db[path]); return snap(path, db[path]); },
      set: async (d, o) => { const after = o?.merge ? apply(db[path], d) : apply({}, d); rules(db[path] ? 'update' : 'create', path, db[path], after); db[path] = material(after); },
      update: async (d) => { if (!db[path]) throw new Error('not-found'); const after = apply(db[path], d); rules('update', path, db[path], after); db[path] = material(after); },
      delete: async () => { delete db[path]; } };
  }
  function collRef(path, filters = []) {
    const q = { doc: (id) => docRef(`${path}/${id || Math.random().toString(36).slice(2, 10)}`),
      where: (f, op, v) => collRef(path, [...filters, [f, op, v]]), orderBy: () => q, limit: () => q,
      get: async () => { const docs = Object.keys(db).filter((k) => k.startsWith(path + '/') && k.split('/').length === path.split('/').length + 1)
        .filter((k) => filters.every(([f, op, v]) => op === 'in' ? v.includes(db[k][f]) : db[k][f] === v)).map((k) => { rules('read', k, db[k]); return snap(k, db[k]); });
        return { docs, empty: !docs.length, size: docs.length }; } };
    return q;
  }
  window.__mkTs = mk;
  // writes in a transaction apply in call order (the app writes customerStats before the ticket, so 'getAfter' sees it)
  // Like real Firestore: tx.set/update are synchronous, and the commit is
  // atomic — if ANY write is denied, all writes roll back and the
  // transaction throws. (An earlier version let a denied write's promise go
  // unawaited, which silently hid denials.)
  const fdb = { collection: (n) => collRef(n), runTransaction: async (fn) => {
    const backup = { ...db }, pend = [];
    const tx = { get: (r) => r.get(), set: (r, d, o) => { pend.push(r.set(d, o)); return tx; }, update: (r, d) => { pend.push(r.update(d)); return tx; } };
    try { const out = await fn(tx); await Promise.all(pend); return out; }
    catch (e) { await Promise.allSettled(pend); for (const k of Object.keys(db)) delete db[k]; Object.assign(db, backup); throw e; }
  } };
  window.dourakFB = { ready: true, db: fdb, get uid() { return window.__who.uid; }, auth: { get currentUser() { return { uid: window.__who.uid, isAnonymous: false }; } } };
})();
