const {onCall, HttpsError} = require('firebase-functions/v2/https');
const {initializeApp} = require('firebase-admin/app');
const {getFirestore, FieldValue} = require('firebase-admin/firestore');
const {getAuth} = require('firebase-admin/auth');
const {onDocumentCreated} = require('firebase-functions/v2/firestore');

initializeApp();
const db = getFirestore();

function requireAuth(request) {
  if (!request.auth) throw new HttpsError('unauthenticated', 'Authentication required.');
  return request.auth.uid;
}

const crypto = require('crypto');

function sha256(value) {
  return crypto.createHash('sha256').update(String(value), 'utf8').digest('hex');
}

function verifyStaffSecret(passcode, secret) {
  if (!secret) return false;
  // Current format: PBKDF2-SHA256 with a per-credential random salt.
  if (secret.algorithm === 'PBKDF2-SHA256' && secret.salt && secret.hash) {
    const iterations = Number(secret.iterations || 310000);
    if (iterations < 200000 || iterations > 1000000) return false;
    const salt = Buffer.from(String(secret.salt), 'base64');
    const derived = crypto.pbkdf2Sync(String(passcode), salt, iterations, 32, 'sha256').toString('hex');
    return crypto.timingSafeEqual(Buffer.from(derived, 'hex'), Buffer.from(String(secret.hash), 'hex'));
  }
  // Legacy SHA-256 is accepted only for one successful login so old accounts
  // can be migrated without exposing their secret to the browser.
  if (secret.passcodeHash && /^[0-9a-f]{64}$/.test(String(secret.passcodeHash))) {
    const a = Buffer.from(sha256(passcode), 'hex');
    const b = Buffer.from(String(secret.passcodeHash), 'hex');
    return a.length === b.length && crypto.timingSafeEqual(a, b);
  }
  return false;
}

function hashStaffSecret(passcode) {
  const salt = crypto.randomBytes(16);
  const iterations = 310000;
  const hash = crypto.pbkdf2Sync(String(passcode), salt, iterations, 32, 'sha256').toString('hex');
  return { algorithm:'PBKDF2-SHA256', iterations, salt:salt.toString('base64'), hash };
}

exports.loginStaff = onCall({enforceAppCheck: true}, async (request) => {
  const uid = requireAuth(request);
  const username = String(request.data?.username || '').trim();
  const passcode = String(request.data?.passcode || '').trim();
  const displayBusinessId = String(request.data?.displayBusinessId || '').trim();
  if (!/^[A-Za-z0-9._-]{3,40}$/.test(username) || !/^\d{6}$/.test(passcode)) {
    throw new HttpsError('invalid-argument', 'Invalid credentials.');
  }

  const loginRef = db.collection('staffLogins').doc(username);
  const loginSnap = await loginRef.get();
  if (!loginSnap.exists) throw new HttpsError('unauthenticated', 'Invalid credentials.');
  const login = loginSnap.data() || {};
  const businessId = String(login.businessId || '');
  const staffId = String(login.staffId || '');
  if (!businessId || !staffId || (displayBusinessId && displayBusinessId !== businessId)) {
    throw new HttpsError('unauthenticated', 'Invalid credentials.');
  }

  const staffRef = db.doc(`businesses/${businessId}/staff/${staffId}`);
  const secretRef = db.doc(`businesses/${businessId}/staffSecrets/${staffId}`);
  const staffSnap = await staffRef.get();
  const secretSnap = await secretRef.get();
  if (!staffSnap.exists || staffSnap.data()?.active === false || !secretSnap.exists) {
    throw new HttpsError('unauthenticated', 'Invalid credentials.');
  }

  const now = Date.now();
  const windowMs = 15 * 60 * 1000;
  const attemptRef = db.doc(`businesses/${businessId}/staffAuth/${staffId}_${uid}`);
  const globalRef = db.doc(`businesses/${businessId}/staffAuthGlobal/${staffId}`);
  let allowed = true;
  let correct = false;
  await db.runTransaction(async tx => {
    const [attemptSnap, globalSnap] = await Promise.all([tx.get(attemptRef), tx.get(globalRef)]);
    const a = attemptSnap.exists ? attemptSnap.data() : {};
    const g = globalSnap.exists ? globalSnap.data() : {};
    const aStart = Number(a.windowStartMs || 0);
    const gStart = Number(g.windowStartMs || 0);
    const aTries = aStart && now - aStart < windowMs ? Number(a.tries || 0) : 0;
    const gTries = gStart && now - gStart < windowMs ? Number(g.tries || 0) : 0;
    if (aTries >= 8 || gTries >= 30) { allowed = false; return; }
    correct = verifyStaffSecret(passcode, secretSnap.data() || {});
    tx.set(attemptRef, { uid, tries: aTries + 1, windowStartMs: aTries ? aStart : now, updatedAt: FieldValue.serverTimestamp() });
    tx.set(globalRef, { staffId, tries: gTries + 1, windowStartMs: gTries ? gStart : now, updatedAt: FieldValue.serverTimestamp() });
  });
  if (!allowed) throw new HttpsError('resource-exhausted', 'Too many attempts.');
  if (!correct) throw new HttpsError('unauthenticated', 'Invalid credentials.');

  // Upgrade legacy SHA-256 credentials after a successful login.
  if (secretSnap.data()?.passcodeHash) {
    await secretRef.set({ ...hashStaffSecret(passcode), updatedAt: FieldValue.serverTimestamp() }, { merge: true });
  }

  const sessionRef = db.doc(`businesses/${businessId}/staffSessions/${uid}`);
  await sessionRef.set({ staffId, createdAt: FieldValue.serverTimestamp(), authMethod: 'appcheck-server-verified' });
  await db.doc(`users/${uid}`).set({ staffOf: { [businessId]: staffId }, lastDourakRole: 'staff', updatedAt: FieldValue.serverTimestamp() }, {merge: true});
  return { businessId, staffId, name: staffSnap.data()?.name || login.name || username };
});

exports.writeAuditLog = onCall({enforceAppCheck: true}, async (request) => {
  const uid = requireAuth(request);
  const type = String(request.data?.type || '').trim();
  const businessId = String(request.data?.businessId || '').trim();
  const targetId = String(request.data?.targetId || '').trim();
  const summary = String(request.data?.summary || '').trim().slice(0, 300);
  const allowed = new Set(['staff_created','staff_updated','staff_deleted','settings_changed','service_changed','queue_action','ownership_action','security_event']);
  if (!allowed.has(type) || !businessId || !summary) throw new HttpsError('invalid-argument','Invalid audit event.');
  const biz = await db.doc(`businesses/${businessId}`).get();
  if (!biz.exists) throw new HttpsError('not-found','Business not found.');
  const ownerId = String(biz.data()?.ownerId || '');
  const isAdmin = await db.doc(`admins/${uid}`).get();
  if (uid !== ownerId && !isAdmin.exists) {
    const sessions = await db.doc(`businesses/${businessId}/staffSessions/${uid}`).get();
    if (!sessions.exists) throw new HttpsError('permission-denied','Not authorized.');
  }
  await db.collection(`businesses/${businessId}/auditLogs`).add({
    actorUid: uid, type, targetId, summary, createdAt: FieldValue.serverTimestamp()
  });
  return {ok:true};
});

exports.takeQueue = onCall({enforceAppCheck: true}, async (request) => {
  // Disabled 2026-09-27: this function used the Admin SDK to write tickets
  // directly, bypassing every check firestore.rules enforces on the client
  // path (confirmationMode approval/otp, maxQueueCapacity, the 3-cancels/24h
  // customerStats limit) — App Check only proves the caller is a real
  // instance of the app, not that it followed the intended flow. index.html
  // never calls this function (no httpsCallable/getFunctions usage found),
  // so it was dead code with a full bypass. Re-enable only after mirroring
  // the same confirmationMode/maxQueueCapacity/customerStats logic the
  // rules use for the direct-Firestore path, and after fixing cancelTicket
  // below to keep queue/current.waitingCount in sync.
  throw new HttpsError('failed-precondition', 'This function is temporarily disabled pending a security review. Use the standard client flow instead.');
});

exports.cancelTicket = onCall({enforceAppCheck: true}, async (request) => {
  // Disabled 2026-09-27: also never decremented queue/current.waitingCount,
  // which would have left the live counter permanently out of sync with
  // actual cancellations. See the note on takeQueue above.
  throw new HttpsError('failed-precondition', 'This function is temporarily disabled pending a security review. Use the standard client flow instead.');
});

exports.recordSecurityEvent = onCall({enforceAppCheck: true}, async (request) => {
  const uid = requireAuth(request);
  const type = String(request.data?.type || '').trim();
  const businessId = String(request.data?.businessId || '').trim();
  const targetId = String(request.data?.targetId || '').trim().slice(0,120);
  const summary = String(request.data?.summary || '').trim().slice(0,240);
  const allowed = new Set(['login_failed','permission_denied','rate_limited','app_check_event','suspicious_activity','ownership_action']);
  if (!allowed.has(type) || !summary) throw new HttpsError('invalid-argument','Invalid security event.');
  if (businessId && !/^[A-Za-z0-9_-]{1,100}$/.test(businessId)) throw new HttpsError('invalid-argument','Invalid business.');
  const key = `${uid}_${new Date().toISOString().slice(0,13)}`;
  const ref = db.collection('securityEvents').doc(key);
  await ref.set({actorUid:uid,type,businessId:businessId||null,targetId:targetId||null,summary,createdAt:FieldValue.serverTimestamp()},{merge:true});
  return {ok:true};
});


function requireRecentAuth(request, maxAgeSeconds = 900) {
  requireAuth(request);
  const authTime = Number(request.auth?.token?.auth_time || 0);
  const nowSeconds = Math.floor(Date.now() / 1000);
  if (!authTime || nowSeconds - authTime > maxAgeSeconds) {
    throw new HttpsError('failed-precondition', 'Recent authentication required.');
  }
}

exports.transferBusinessOwnership = onCall({enforceAppCheck: true}, async (request) => {
  const uid = requireAuth(request);
  requireRecentAuth(request, 900);
  const businessId = String(request.data?.businessId || '').trim();
  const targetUid = String(request.data?.targetUid || '').trim();
  if (!businessId || !targetUid || targetUid === uid) throw new HttpsError('invalid-argument', 'Invalid ownership transfer.');
  const bizRef = db.doc(`businesses/${businessId}`);
  const biz = await bizRef.get();
  if (!biz.exists) throw new HttpsError('not-found', 'Business not found.');
  if (String(biz.data()?.ownerId || '') !== uid) throw new HttpsError('permission-denied', 'Only the current owner can transfer ownership.');
  try { await getAuth().getUser(targetUid); } catch { throw new HttpsError('not-found', 'Target account not found.'); }
  await db.runTransaction(async tx => {
    const fresh = await tx.get(bizRef);
    if (String(fresh.data()?.ownerId || '') !== uid) throw new HttpsError('aborted', 'Ownership changed. Try again.');
    tx.update(bizRef, { ownerId: targetUid, updatedAt: FieldValue.serverTimestamp() });
    tx.set(db.doc(`businesses/${businessId}/ownershipTransfers/${Date.now()}_${uid}`), { fromUid: uid, toUid: targetUid, createdAt: FieldValue.serverTimestamp() });
  });
  await db.collection(`businesses/${businessId}/auditLogs`).add({ actorUid: uid, type: 'ownership_action', targetId: targetUid, summary: 'Business ownership transferred', createdAt: FieldValue.serverTimestamp() });
  return { ok: true, businessId, targetUid };
});
