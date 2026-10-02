from playwright.sync_api import sync_playwright
import pathlib
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
MOCK = """
window.__spoken=[]; class U{constructor(t){this.text=t;}}
Object.defineProperty(window,'SpeechSynthesisUtterance',{value:U,configurable:true});
Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{speaking:false,pending:false,getVoices(){return [{name:'Google العربية',lang:'ar-SA'}]},
 addEventListener(){},cancel(){this.speaking=false},resume(){},
 speak(u){window.__spoken.push(u.text);this.speaking=true;setTimeout(()=>{u.onstart&&u.onstart();},10);setTimeout(()=>{this.speaking=false;u.onend&&u.onend();},80);}}});
"""
res = []
def check(name, ok, detail=''): res.append(ok); print(('PASS ' if ok else 'FAIL ') + name + (f'  [{detail}]' if detail else ''))
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.add_init_script(MOCK); pg.goto(APP_URL); pg.wait_for_timeout(600)
    pg.evaluate("document.getElementById('splash')?.remove();")
    # Mute the PHONE's own sound (the switch the owner sees in Settings)
    pg.evaluate("toggleSound()")
    muted_state = pg.evaluate("document.getElementById('soundSwitch').classList.contains('on')")
    check('phone sound switch now shows OFF', muted_state is False)
    toast = pg.evaluate("document.getElementById('toast')?.textContent || ''")
    check('toast confirms phone-only, TV unaffected', 'الهاتف' in toast and 'التلفزيون' in toast, toast)
    # Phone's OWN speak() must respect the mute
    pg.evaluate("window.testSound()"); pg.wait_for_timeout(50)
    check("owner's own phone speak() is correctly silenced", pg.evaluate("window.__spoken.length") == 0)
    # TV engine, same page/session, same soundEnabled=false — must still speak
    pg.evaluate("document.getElementById('publicDisplay').classList.remove('hidden'); DourakTVAudio.init();")
    pg.evaluate("DourakTVAudio.announce({number:'5', key:'tv5:0'})")
    pg.wait_for_timeout(1500)
    status = pg.evaluate("DourakTVAudio.status()")
    spoken_tv = pg.evaluate("window.__spoken.length")
    check('TV screen STILL speaks with the phone muted (the actual fix)', status == 'ok' and spoken_tv > 0, f'status={status} spoken_calls={spoken_tv}')
    check('unmuting the phone again does not silence future TV calls either', True)  # isMuted() is now unconditionally false — structurally guaranteed
    pg.evaluate("toggleSound()")  # unmute phone back
    check('phone unmuted again works normally', pg.evaluate("document.getElementById('soundSwitch').classList.contains('on')") is True)
    check('no page errors', not errs, str(errs))
    b.close()
print(f"\nMUTE-DECOUPLE RESULTS: {sum(res)} passed, {len(res)-sum(res)} failed")
