import os, pathlib
APP_URL = pathlib.Path(__file__).resolve().parent.parent.joinpath('index.html').as_uri()
from playwright.sync_api import sync_playwright
UAS={'iPhone':'Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1',
     'Android':'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36',
     'WhatsApp in-app':'Mozilla/5.0 (Linux; Android 14; SM-S918B; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/124.0 Mobile Safari/537.36 WhatsApp/2.24'}
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,ua in UAS.items():
        pg=b.new_page(user_agent=ua,viewport={'width':390,'height':844}); errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
        pg.goto(APP_URL); pg.wait_for_timeout(700); pg.evaluate("document.getElementById('splash')?.remove()")
        visible=pg.evaluate("!document.querySelector('.install-app-btn').classList.contains('hidden')")
        pg.click('.install-app-btn'); pg.wait_for_timeout(300)
        steps=pg.evaluate("[...document.querySelectorAll('.install-steps li')].map(l=>l.textContent)")
        print(f'[{name}] button visible={visible} | guide steps={steps} | errors={errs}')
        if name=='iPhone': pg.evaluate("closeModal()"); pg.wait_for_timeout(200); pg.screenshot(path='raw/install_btn.png')
        pg.close()
    pg=b.new_page(user_agent=UAS['Android'])
    pg.add_init_script("localStorage.setItem('tbSetup', JSON.stringify({businessId:'b1',name:'صالون الأمير',address:'دبي'})); localStorage.setItem('dourakBusinessId','b1');")
    pg.goto(APP_URL); pg.wait_for_timeout(600)
    pg.evaluate("""window.__prompted=0; const e=new Event('beforeinstallprompt',{cancelable:true}); e.prompt=()=>{window.__prompted++}; e.userChoice=Promise.resolve({outcome:'accepted'}); window.dispatchEvent(e);""")
    pg.evaluate("document.getElementById('splash')?.remove()"); pg.click('.install-app-btn'); pg.wait_for_timeout(200)
    print('[Android real prompt] native prompt shown:', pg.evaluate("window.__prompted"), '| guide opened instead:', pg.evaluate("!!document.querySelector('.install-steps')"))
    pg.evaluate("""window.__opens=[]; window.open=(u)=>{window.__opens.push(u); return {closed:false,location:{},focus(){},close(){}}};
      localStorage.setItem('dourakBusinessId','b1'); window.setup={businessId:'b1',name:'صالون الأمير',address:'دبي'};
      window.__ownerQueueRows=[{id:'t1',number:13,customerPhone:'0501234567',type:'queue'}];""")
    sync=pg.evaluate("(()=>{ sendTokenWhatsapp('t1'); return window.__opens.length; })()")
    print('[token -> WhatsApp] opened synchronously inside the tap:', sync==1, '|', (pg.evaluate("window.__opens[0]") or '')[:70])
    pg.evaluate("window.open=()=>null; dourakOpenExternal('https://wa.me/971501234567')"); pg.wait_for_timeout(200)
    print('[blocked popup] fallback sheet link:', pg.evaluate("document.querySelector('#sheet a[target=_blank]')?.getAttribute('href')"))
    b.close()
