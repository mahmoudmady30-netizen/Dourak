/* Dourak operational feature flags. These are UX/availability controls only;
   Firestore rules and Cloud Functions remain the authorization boundary. */
window.DOURAK_FEATURES = Object.assign({
  pwa: true,
  offlineRecovery: true,
  duplicateActionGuard: true,
  securityActivity: true,
  advancedDiagnostics: true,
  onlineBooking: true,
  ratings: true,
  whatsapp: true,
  staffManagement: true,
  ownershipTransfer: true
}, window.DOURAK_FEATURES || {});
