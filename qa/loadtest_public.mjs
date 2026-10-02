import assert from 'node:assert/strict';
const base = process.env.DOURAK_BASE_URL;
if (!base) { console.log('SKIP: DOURAK_BASE_URL not set'); process.exit(0); }
const n = Math.max(1, Math.min(50, Number(process.env.LOAD_CONCURRENCY || 10)));
const started = Date.now();
const results = await Promise.all(Array.from({length:n}, async () => {
  const t = Date.now();
  try { const r = await fetch(base, {redirect:'follow'}); return {ok:r.ok, ms:Date.now()-t, status:r.status}; }
  catch (e) { return {ok:false, ms:Date.now()-t, error:String(e)}; }
}));
const failed = results.filter(x => !x.ok);
const avg = Math.round(results.reduce((a,x)=>a+x.ms,0)/results.length);
console.log(JSON.stringify({requests:n,failed:failed.length,avgMs:avg,totalMs:Date.now()-started,results}, null, 2));
assert.equal(failed.length, 0);
