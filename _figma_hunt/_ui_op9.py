# -*- coding: utf-8 -*-
import io, sys, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
FK='5Gs4PaTz11Hlk2sqVnidBG'
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
    ctx=b.new_context(viewport={'width':1600,'height':900})
    ctx.add_cookies(cookies)
    page=ctx.new_page()
    page.goto(f'https://www.figma.com/file/{FK}/', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(30000)
    info=page.evaluate('''() => {
      const out={toolbelt:[], title:document.title, body:document.body.innerText.slice(0,300)};
      document.querySelectorAll('[class*="toolbelt_mode_segmented_control"] *').forEach(e=>{
        const t=e.textContent.trim();
        if(t&&t.length<20&&e.children.length===0){ const r=e.getBoundingClientRect(); out.toolbelt.push({t, x:Math.round(r.x+r.width/2), y:Math.round(r.y+r.height/2), w:Math.round(r.width), h:Math.round(r.height)}); }
      });
      return out;
    }''')
    print('TITLE:', info['title'])
    print('TOOLBELT:', json.dumps(info['toolbelt'],ensure_ascii=False))
    print('BODY:', info['body'][:250])
    page.screenshot(path='ui_5gs.png')
    b.close()
