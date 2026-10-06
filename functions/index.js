const {onCall, HttpsError} = require('firebase-functions/v2/https');
const {initializeApp} = require('firebase-admin/app');
const {getFirestore, FieldValue} = require('firebase-admin/firestore');

initializeApp();
const db = getFirestore();

function requireAuth(request) {
  if (!request.auth) throw new HttpsError('unauthenticated', 'Authentication required.');
  return request.auth.uid;
}

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
