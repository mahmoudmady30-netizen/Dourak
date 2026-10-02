/* Privacy-safe client telemetry hooks. No customer content is collected. */
(function(){
  const endpoint = window.DOURAK_MONITORING_ENDPOINT || '';
  function report(kind, error){
    try {
      const payload={kind, message:String(error?.message||error||'unknown').slice(0,240), path:location.pathname, build:window.DOURAK_BUILD||'V110', online:navigator.onLine, ts:Date.now()};
      window.__dourakLastError=payload;
      if(endpoint && navigator.sendBeacon) navigator.sendBeacon(endpoint, JSON.stringify(payload));
    } catch(_){}
  }
  window.addEventListener('error', e=>report('window_error', e.error||e.message));
  window.addEventListener('unhandledrejection', e=>report('unhandled_rejection', e.reason));
  window.dourakReportError=report;
})();
