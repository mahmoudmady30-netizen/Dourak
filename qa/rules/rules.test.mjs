// Firestore rules tests, run against Google's real emulator in GitHub
// Actions (.github/workflows/firestore-rules.yml). Each "allows" test mirrors
// the exact write shape the app sends; each "blocks" test is a write or read
// that the V107 rules must refuse.
import { test, before, beforeEach, after } from 'node:test';
import { readFileSync } from 'node:fs';
import { initializeTestEnvironment, assertSucceeds, assertFails } from '@firebase/rules-unit-testing';
import firebase from 'firebase/compat/app';
import 'firebase/compat/firestore';

const FV = firebase.firestore.FieldValue;
const ts = () => FV.serverTimestamp();
let env;

const OWNER = 'owner1', CUST = 'cust1', OTHER = 'other1', ADMIN = 'admin1', STAFFDEV = 'staffDevice1';
const perm = (uid) => env.authenticatedContext(uid, { firebase: { sign_in_provider: 'password' } }).firestore();
const anon = (uid) => env.authenticatedContext(uid, { firebase: { sign_in_provider: 'anonymous' } }).firestore();

before(async () => {
  env = await initializeTestEnvironment({
    projectId: 'demo-dourak',
    firestore: { rules: readFileSync(new URL('../../firestore.rules', import.meta.url), 'utf8'), host: '127.0.0.1', port: 8080 },
  });
});
after(async () => { await env?.cleanup(); });

beforeEach(async () => {
  await env.clearFirestore();
  await env.withSecurityRulesDisabled(async (ctx) => {
    const db = ctx.firestore();
    await db.doc('admins/' + ADMIN).set({ note: 'granted in console' });
    await db.doc('businesses/b1').set({ name: 'Salon', ownerId: OWNER, active: true, confirmationMode: 'auto', businessCode: 'DRK-AAAAAAA' });
    await db.doc('businessCodes/DRK-AAAAAAA').set({ businessId: 'b1' });
    await db.doc('businesses/b1/services/s1').set({ name: 'Cut', duration: 30, price: 40, active: true });
    await db.doc('businesses/b1/queue/current').set({ nextNumber: 5, currentNumber: 2, waitingCount: 1, servedCount: 1 });
    await db.doc('businesses/b1/staff/st1').set({ name: 'Sara', role: 'employee', active: true, username: 'sara123456' });
    await db.doc('businesses/b1/staffSecrets/st1').set({ passcode: '123456' });
    await db.doc('staffLogins/sara123456').set({ businessId: 'b1', staffId: 'st1', name: 'Sara' });
    await db.doc('businesses/b1/ticketContacts/tOld').set({ customerId: 'someoneElse', customerName: 'Mona', customerPhone: '0500000000' });
    await db.doc('businesses/b1/otpSecrets/tOld').set({ code: '654321' });
    await db.doc('businesses/b2').set({ name: 'Clinic', ownerId: 'owner2', active: true, confirmationMode: 'otp' });
    await db.doc('businesses/b2/services/s1').set({ name: 'Visit', duration: 15, price: 0, active: true });
    await db.doc('businesses/b2/queue/current').set({ nextNumber: 1, currentNumber: 0, waitingCount: 0, servedCount: 0 });
    await db.doc('businesses/b3').set({ name: 'Full', ownerId: 'owner3', active: true, maxQueueCapacity: 1 });
    await db.doc('businesses/b3/services/s1').set({ name: 'X', active: true });
    await db.doc('businesses/b3/queue/current').set({ nextNumber: 2, currentNumber: 0, waitingCount: 1, servedCount: 0 });
    await db.doc('users/' + OTHER).set({ email: 'other@x.com', phone: '0501111111' });
    await db.doc('bookings/bk1').set({ customerId: CUST, businessId: 'b1', ticketId: 'bk1', status: 'waiting' });
  });
});

// The exact transaction the app runs for "خد دور".
async function join(db, bid, { status = 'waiting', serviceId = 's1', linkTicket = true } = {}) {
  const qref = db.doc(`businesses/${bid}/queue/current`);
  const tref = db.collection(`businesses/${bid}/queueTickets`).doc();
  await db.runTransaction(async (tx) => {
    const q = (await tx.get(qref)).data() || {};
    const number = Number(q.nextNumber || 1);
    const upd = { nextNumber: number + 1, currentNumber: Number(q.currentNumber || 0), waitingCount: Number(q.waitingCount || 0) + 1, servedCount: Number(q.servedCount || 0), updatedAt: ts() };
    if (linkTicket) upd.lastIssuedTicketId = tref.id;
    tx.set(qref, upd, { merge: true });
    tx.set(tref, { customerId: CUST, businessId: bid, serviceId, number, status, createdAt: ts(), businessName: 'B', serviceName: 'S', duration: 30, price: 40 });
    tx.set(db.doc(`bookings/${tref.id}`), { customerId: CUST, businessId: bid, serviceId, ticketId: tref.id, number, status: 'waiting', createdAt: ts(), businessName: 'B', serviceName: 'S', type: 'queue' });
  });
  return tref;
}

// ---------------------------------------------------------------- admin
test('blocks a user from granting themselves admin', async () => {
  await assertFails(perm(OTHER).doc('users/' + OTHER).set({ role: 'admin' }, { merge: true }));
});
test('allows role customer on own user doc', async () => {
  await assertSucceeds(perm(OTHER).doc('users/' + OTHER).set({ role: 'customer' }, { merge: true }));
});
test('blocks writes to the admins list from any client', async () => {
  await assertFails(perm(OTHER).doc('admins/' + OTHER).set({ x: 1 }));
});
test('allows a console-granted admin to read another user', async () => {
  await assertSucceeds(perm(ADMIN).doc('users/' + OTHER).get());
});
test('blocks a regular user from reading another user', async () => {
  await assertFails(perm(CUST).doc('users/' + OTHER).get());
});

// ---------------------------------------------------------------- staff
test('blocks self-declared staff membership from reading customer contacts', async () => {
  const db = anon(STAFFDEV);
  await assertSucceeds(db.doc('users/' + STAFFDEV).set({ staffOf: { b1: 'st1' } }, { merge: true }));
  await assertFails(db.doc('businesses/b1/ticketContacts/tOld').get());
  await assertFails(db.doc('businesses/b1/otpSecrets/tOld').get());
});
test('blocks anyone but the owner from reading staff passcodes', async () => {
  await assertFails(anon(STAFFDEV).doc('businesses/b1/staffSecrets/st1').get());
  await assertSucceeds(perm(OWNER).doc('businesses/b1/staffSecrets/st1').get());
});
test('blocks storing a passcode on the public staff record', async () => {
  await assertFails(perm(OWNER).doc('businesses/b1/staff/st2').set({ name: 'X', role: 'employee', active: true, passcode: '111111' }));
  await assertFails(perm(OWNER).doc('staffLogins/x999').set({ businessId: 'b1', staffId: 'st2', name: 'X', passcode: '111111' }));
});
test('allows staff login with the right passcode, then staff access', async () => {
  const db = anon(STAFFDEV);
  await assertSucceeds(db.doc('businesses/b1/staffAuth/st1').set({ uid: STAFFDEV, guess: '123456', tries: 1, windowStart: ts() }));
  await assertSucceeds(db.doc(`businesses/b1/staffSessions/${STAFFDEV}`).set({ staffId: 'st1', createdAt: ts() }));
  await assertSucceeds(db.doc('businesses/b1/ticketContacts/tOld').get());
});
test('blocks a staff session after a wrong passcode', async () => {
  const db = anon(STAFFDEV);
  await assertSucceeds(db.doc('businesses/b1/staffAuth/st1').set({ uid: STAFFDEV, guess: '000000', tries: 1, windowStart: ts() }));
  await assertFails(db.doc(`businesses/b1/staffSessions/${STAFFDEV}`).set({ staffId: 'st1', createdAt: ts() }));
});
test('limits login attempts to 8 per 15 minutes', async () => {
  const db = anon(STAFFDEV);
  await assertSucceeds(db.doc('businesses/b1/staffAuth/st1').set({ uid: STAFFDEV, guess: '000000', tries: 1, windowStart: ts() }));
  for (let i = 2; i <= 8; i++) await assertSucceeds(db.doc('businesses/b1/staffAuth/st1').set({ uid: STAFFDEV, guess: '00000' + i, tries: FV.increment(1) }, { merge: true }));
  await assertFails(db.doc('businesses/b1/staffAuth/st1').set({ uid: STAFFDEV, guess: '000009', tries: FV.increment(1) }, { merge: true }));
  await assertFails(db.doc('businesses/b1/staffAuth/st1').set({ uid: STAFFDEV, guess: '000009', tries: 1, windowStart: ts() }));
});

// ---------------------------------------------------------------- queue
test('allows the normal join transaction', async () => {
  await assertSucceeds(join(perm(CUST), 'b1'));
});
test('blocks a join whose counter change names no ticket', async () => {
  await assertFails(join(perm(CUST), 'b1', { linkTicket: false }));
});
test('blocks moving the counters without a ticket', async () => {
  const db = perm(OTHER);
  await assertFails(db.doc('businesses/b1/queue/current').set({ nextNumber: 6, waitingCount: 2, lastIssuedTicketId: 'nope' }, { merge: true }));
  await assertFails(db.doc('businesses/b1/queue/current').set({ waitingCount: 0, lastCancelledTicketId: 'nope' }, { merge: true }));
});
test('blocks skipping the owner OTP confirmation', async () => {
  await assertFails(join(perm(CUST), 'b2', { status: 'waiting' }));
  await assertSucceeds(join(perm(CUST), 'b2', { status: 'pending_otp' }));
});
test('blocks joining a full queue', async () => {
  await assertFails(join(perm(CUST), 'b3'));
});
test('blocks a ticket for a service that does not exist', async () => {
  await assertFails(join(perm(CUST), 'b1', { serviceId: 'ghost' }));
});
test('allows the customer cancel transaction', async () => {
  const t = await join(perm(CUST), 'b1');
  const db = perm(CUST);
  await assertSucceeds(db.runTransaction(async (tx) => {
    const q = (await tx.get(db.doc('businesses/b1/queue/current'))).data();
    tx.set(db.doc(`businesses/b1/customerStats/${CUST}`), { cancels: 1, windowStart: ts(), lastCancelledTicketId: t.id });
    tx.update(db.doc(t.path), { status: 'cancelled', cancelledAt: ts(), cancellationReason: 'x' });
    tx.set(db.doc('businesses/b1/queue/current'), { waitingCount: q.waitingCount - 1, lastCancelledTicketId: t.id, updatedAt: ts() }, { merge: true });
  }));
});
test('allows the owner call-next style counter update', async () => {
  await assertSucceeds(perm(OWNER).doc('businesses/b1/queue/current').set({ currentNumber: 3, waitingCount: 0, servedCount: 2 }, { merge: true }));
});
test('allows booking an appointment', async () => {
  const db = perm(CUST);
  const qref = db.doc('businesses/b1/queue/current'), tref = db.collection('businesses/b1/queueTickets').doc();
  await assertSucceeds(db.runTransaction(async (tx) => {
    const q = (await tx.get(qref)).data();
    const number = Number(q.nextAppointmentNumber || 1);
    tx.set(qref, { nextAppointmentNumber: number + 1, nextNumber: q.nextNumber, currentNumber: q.currentNumber, waitingCount: q.waitingCount, servedCount: q.servedCount, lastIssuedTicketId: tref.id, updatedAt: ts() }, { merge: true });
    tx.set(tref, { customerId: CUST, businessId: 'b1', serviceId: 's1', number, status: 'scheduled', type: 'appointment', appointmentAt: Date.now() + 3600000, createdAt: ts(), businessName: 'B', serviceName: 'S', duration: 30, price: 40 });
    tx.set(db.doc(`bookings/${tref.id}`), { customerId: CUST, businessId: 'b1', serviceId: 's1', ticketId: tref.id, number, status: 'waiting', createdAt: ts(), businessName: 'B', serviceName: 'S', type: 'appointment' });
  }));
});

// ---------------------------------------------------------------- privacy
test('blocks reading someone else\'s booking', async () => {
  await assertFails(perm(OTHER).doc('bookings/bk1').get());
});
test('allows the customer and the business owner to read a booking', async () => {
  await assertSucceeds(perm(CUST).doc('bookings/bk1').get());
  await assertSucceeds(perm(OWNER).collection('bookings').where('businessId', '==', 'b1').get());
});

// ---------------------------------------------------------------- business codes
test('blocks taking another business\'s code', async () => {
  await env.withSecurityRulesDisabled(async (ctx) => { await ctx.firestore().doc('businesses/b4').set({ name: 'Mine', ownerId: OTHER, active: true }); });
  const db = perm(OTHER);
  const batch = db.batch();
  batch.update(db.doc('businesses/b4'), { businessCode: 'DRK-AAAAAAA' });
  batch.set(db.doc('businessCodes/DRK-AAAAAAA'), { businessId: 'b4' });
  await assertFails(batch.commit());
});
test('allows creating a business together with its own new code', async () => {
  const db = perm(OTHER);
  const batch = db.batch();
  batch.set(db.doc('businesses/b5'), { name: 'New', ownerId: OTHER, active: true, businessCode: 'DRK-BBBBBBB', createdAt: ts() });
  batch.set(db.doc('businessCodes/DRK-BBBBBBB'), { businessId: 'b5', createdAt: ts() });
  await assertSucceeds(batch.commit());
});

// ---------------------------------------------------------------- messages / notifications
test('blocks a customer posting a message as the owner', async () => {
  const db = perm(CUST);
  await assertSucceeds(db.doc('conversations/c1').set({ customerId: CUST, businessId: 'b1', ticketId: 't', lastMessage: 'hi', updatedAt: ts() }));
  await assertFails(db.doc('conversations/c1/messages/m1').set({ senderId: CUST, senderRole: 'owner', text: 'x', createdAt: ts(), read: false }));
  await assertSucceeds(db.doc('conversations/c1/messages/m2').set({ senderId: CUST, senderRole: 'customer', text: 'x', createdAt: ts(), read: false }));
});
test('blocks oversized notification text', async () => {
  const db = perm(CUST);
  await assertFails(db.doc(`users/${OWNER}/notifications/n1`).set({ type: 'x', businessId: 'b1', ticketId: 't', title: 'T', body: 'x'.repeat(1001), read: false, createdAt: ts() }));
  await assertSucceeds(db.doc(`users/${OWNER}/notifications/n2`).set({ type: 'x', businessId: 'b1', ticketId: 't', title: 'T', body: 'ok', read: false, createdAt: ts() }));
});
