# -*- coding: utf-8 -*-
import io, sys, json, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_A_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
pairs=[p.split('=',1) for p in raw.split('; ') if '=' in p]
cookies=[]
for k,v in pairs:
    c={'name':k,'value':v,'path':'/','secure':True,'sameSite':'Lax'}
    if not k.startswith('__Host-'):
        c['domain']='.figma.com'
    else:
        c['url']='https://www.figma.com'; del c['path']
    cookies.append(c)
with sync_playwright() as p:
    b=p.chromium.launch(headless=False)
    ctx=b.new_context(viewport={'width':1400,'height':800})
    ctx.add_cookies(cookies)
    page=ctx.new_page()
    ok=False
    for url in ['https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm/Dev-Mode-Test-File','https://www.figma.com/files']:
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=45000)
            ok=True
            print('loaded:', url)
            break
        except Exception as e:
            print('goto fail:', str(e)[:80]); time.sleep(8)
    if ok:
        page.wait_for_timeout(12000)
        r=page.evaluate("""async () => {
          const resp = await fetch('/api/mcp/session_token_exchange', {
            method:'POST',
            headers:{'Content-Type':'application/json','Accept':'application/json'},
            body: JSON.stringify({client:'MCP_CLIENT_DESKTOP_PROXY'})
          });
          const txt = await resp.text();
          return {status: resp.status, headers: Object.fromEntries(resp.headers.entries()), body: txt.slice(0,600)};
        }""")
        print(json.dumps(r,ensure_ascii=False)[:1400])
    b.close()
