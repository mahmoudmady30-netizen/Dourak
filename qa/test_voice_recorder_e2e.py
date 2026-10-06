import os, pathlib
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
from playwright.sync_api import sync_playwright
import base64, struct, json
MOCK_DB = """
window.__store = window.__store || {};
window.firebase = {firestore:{FieldValue:{serverTimestamp:()=>({toMillis:()=>Date.now()})}}};
const vpColl = { where(){ return { get: async()=>({docs:Object.entries(window.__store).map(([id,v])=>({id,data:()=>v}))}) }; },
  doc(id){ return { set: async(v)=>{ window.__store[id]=v; }, delete: async()=>{ delete window.__store[id]; } }; } };
window.dourakFB = { ready:true, db:{ collection(){ return { doc(){ return { collection(){ return vpColl; }, update: async()=>{} }; } }; } } };
localStorage.setItem('dourakBusinessId','b1'); window.setup={businessId:'b1'}; window.__dourakDisplayBid='b1';
"""
with sync_playwright() as p:
    b=p.chromium.launch(args=['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream','--autoplay-policy=no-user-gesture-required'])
    ctx=b.new_context(permissions=['microphone']); pg=ctx.new_page(); errs=[]
    pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.goto(APP_URL); pg.wait_for_timeout(600)
    pg.evaluate("document.getElementById('splash')?.remove();"); pg.evaluate(MOCK_DB)
    # OWNER PHONE: open recorder, record 5 clips (prefix, 1, 2, suffix, 0) with the fake mic (auto-stops at 3.5s; we stop at 1.2s)
    pg.evaluate("openVoiceRecorder()"); pg.wait_for_timeout(400)
    for k in ['prefix','1','2','suffix']:
        pg.evaluate(f"vrToggle('{k}')"); pg.wait_for_timeout(1200); pg.evaluate(f"vrToggle('{k}')"); pg.wait_for_timeout(1500)
    rows = pg.evaluate("[...document.querySelectorAll('.vr-row small')].slice(0,4).map(e=>e.textContent)")
    prog = pg.evaluate("document.querySelector('.vr-progress')?.textContent")
    store = pg.evaluate("Object.fromEntries(Object.entries(window.__store).map(([k,v])=>[k,{lang:v.lang,key:v.key,ms:v.durationMs,len:v.dataUrl.length,head:v.dataUrl.slice(0,40)}]))")
    print('recorder progress:', prog); print('row states:', rows); print('saved docs:', json.dumps(store, ensure_ascii=False))
    wav = pg.evaluate("window.__store['ar_1'].dataUrl"); raw = base64.b64decode(wav.split(',')[1])
    print('WAV check: riff=%s fmt=%s channels=%d rate=%d bits=%d bytes=%d' % (raw[:4], raw[8:12], struct.unpack('<H',raw[22:24])[0], struct.unpack('<I',raw[24:28])[0], struct.unpack('<H',raw[34:36])[0], len(raw)))
    pg.evaluate("closeModal()")
    # TV: no speech engine at all; announce a call → must play the recorded clips
    pg.evaluate("delete window.speechSynthesis; delete window.SpeechSynthesisUtterance;")
    pg.evaluate("""window.__played=0; const C=window.__dourakAudioCtx; const orig=C.createBufferSource.bind(C);
      C.createBufferSource=function(){ const s=orig(); const st=s.start.bind(s); s.start=function(...a){ if(s.buffer&&s.buffer.length>50) window.__played++; return st(...a); }; return s; };
      document.getElementById('publicDisplay').classList.remove('hidden'); DourakTVAudio.init();
      DourakTVAudio.announce({number:12,key:'t12:0'});""")
    pg.wait_for_timeout(6000)
    print('TV result:', pg.evaluate("({status:DourakTVAudio.status(), clipsPlayed:window.__played, hint:document.getElementById('pdAudioState')?.textContent})"))
    print('page errors:', errs); b.close()
