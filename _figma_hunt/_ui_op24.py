# -*- coding: utf-8 -*-
import io, sys, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
raw=io.open('ws_cookie_B_new.txt',encoding='utf-8').read().strip().replace('\n','; ')
pairs=[p.split('=',1) for p in raw.split('; ') if '=' in p]
cookies=[]
for k,v in pairs:
    c={'name':k,'value':v,'path':'/','secure':True,'sameSite':'Lax'}
    if not k.startswith('__Host-'):
        c['domain']='.figma.com'
    else:
        c['url']='https://www.figma.com'; del c['path']
    cookies.append(c)
hits=[]
def on_resp(resp):
    u=resp.url
    if any(x in u for x in ('code_connect','suggestion','handoff','component_browser','library')):
        hits.append({'url':u[:200], 'status':resp.status})
with sync_playwright() as p:
    b=p.chromium.launch(headless=False)
    ctx=b.new_context(viewport={'width':1600,'height':900})
    ctx.add_cookies(cookies)
    page=ctx.new_page()
    page.on('response', on_resp)
    page.goto('https://www.figma.com/file/ucha7bf05fJ81CJZVoruo0/Flowbite', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(35000)
    print('HITS:', len(hits))
    for h in hits[:25]: print(' ', h['status'], h['url'])
    b.close()
