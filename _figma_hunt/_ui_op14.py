# -*- coding: utf-8 -*-
import io, sys, json
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
    ctx=b.new_context(viewport={'width':1600,'height':900})
    ctx.add_cookies(cookies)
    page=ctx.new_page()
    page.goto('https://www.figma.com/design/9MmnJNhhwn2hDNEqLoMToP/Untitled', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(30000)
    info=page.evaluate('''() => {
      const root=document.querySelector('.toolbelt--root--K5bkV, [class*="toolbelt--root"]');
      if(!root) return 'no toolbelt root';
      const walk=(el,arr)=>{ const r=el.getBoundingClientRect(); const cs=getComputedStyle(el);
        arr.push({cls:(el.className||'').toString().slice(0,60), x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height), display:cs.display, vis:cs.visibility, op:cs.opacity, pos:cs.position, z:cs.zIndex});
        if(el.parentElement) walk(el.parentElement,arr); };
      const arr=[]; walk(root,arr);
      return arr.slice(0,8);
    }''')
    print('TOOLBELT CHAIN:', json.dumps(info,ensure_ascii=False)[:1200])
    # 画布中心点击尝试(选中画布)
    page.mouse.click(800, 450)
    page.wait_for_timeout(3000)
    # 按 R 选矩形工具, 拖拽画矩形
    page.keyboard.press('r')
    page.wait_for_timeout(1000)
    page.mouse.move(600, 300); page.mouse.down(); page.mouse.move(1000, 500, steps=10); page.mouse.up()
    page.wait_for_timeout(3000)
    sel=page.evaluate('''() => {
      const els=[...document.querySelectorAll('[class*="selection"],[aria-label*="Selection"],[data-testid*="sel"]')];
      const out=[];
      els.forEach(e=>{ const t=(e.innerText||'').trim(); if(t&&t.length<80) out.push(t); });
      return out.slice(0,5);
    }''')
    print('SELECTION:', json.dumps(sel,ensure_ascii=False))
    # Ctrl+Alt+K 创建组件
    page.keyboard.press('Control+Alt+k')
    page.wait_for_timeout(4000)
    print('AFTER K:', page.evaluate('document.body.innerText.includes("Create component") || document.body.innerText.includes("Component")'))
    page.screenshot(path='ui_rect.png')
    b.close()
