import os, pathlib
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
from playwright.sync_api import sync_playwright
MOCK = """
window.__spoken=[];
class U{constructor(t){this.text=t;}}
Object.defineProperty(window,'SpeechSynthesisUtterance',{value:U,configurable:true});
Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{speaking:false,pending:false,getVoices(){return [{name:'Google العربية',lang:'ar-SA'}]},
 addEventListener(){},cancel(){this.speaking=false},resume(){},
 speak(u){window.__spoken.push(u.text);this.speaking=true;setTimeout(()=>{u.onstart&&u.onstart();},10);setTimeout(()=>{this.speaking=false;u.onend&&u.onend();},80);}}});
"""
STUB = """
class U{constructor(t){this.text=t;}}
Object.defineProperty(window,'SpeechSynthesisUtterance',{value:U,configurable:true});
Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{speaking:false,pending:false,getVoices(){return []},addEventListener(){},cancel(){},resume(){},speak(u){/* TV stub: accepts, never speaks, no events */}}});
"""
def run(name, pre, script, wait=1800, args=['--autoplay-policy=no-user-gesture-required']):
    with sync_playwright() as p:
        b=p.chromium.launch(args=args); pg=b.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append(str(e)))
        if pre: pg.add_init_script(pre)
        pg.goto(APP_URL); pg.wait_for_timeout(500)
        pg.evaluate("document.getElementById('splash')?.remove();document.getElementById('publicDisplay').classList.remove('hidden');")
        pg.evaluate(script); pg.wait_for_timeout(wait)
        out=pg.evaluate("({spoken:window.__spoken||null,status:DourakTVAudio.status(),hint:document.getElementById('pdAudioState')?.textContent,btn:document.getElementById('pdAudioBtn')?.textContent,ctx:window.__dourakAudioCtx?.state})")
        print(f'[{name}]',out,'| page errors:',errs); b.close()
run('dedupe+recall (speech works)', MOCK, """
DourakTVAudio.init(); DourakTVAudio.unlock({silent:true});
DourakTVAudio.announce({number:12,key:'t1:0'});
setTimeout(()=>DourakTVAudio.announce({number:12,key:'t1:0'}),900);   // duplicate snapshot
setTimeout(()=>DourakTVAudio.announce({number:12,key:'t1:777',kind:'recall'}),1100); // recall
""", wait=3500)
run('newest call wins (no pile-up)', MOCK, """
DourakTVAudio.init();
[5,6,7,8].forEach((n,i)=>DourakTVAudio.announce({number:n,key:'t'+n+':0'}));
""", wait=2500)
run('TV with NO speechSynthesis (your case)', "delete window.speechSynthesis; delete window.SpeechSynthesisUtterance;", """
DourakTVAudio.init(); DourakTVAudio.announce({number:31,key:'x:0'});
""", wait=9000)
run('TV stub engine (API present, silent)', STUB, """
DourakTVAudio.init(); DourakTVAudio.announce({number:44,key:'y:0'});
""", wait=11000)
run('locked (strict autoplay, no tap yet)', None, "DourakTVAudio.init();", wait=500, args=['--autoplay-policy=user-gesture-required'])
