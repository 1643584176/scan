# -*- coding: utf-8 -*-
import io, sys, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
FK='bv2nMIdFf4u3dESGail4sm'
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
def is_dev(page):
    return page.evaluate('document.body.innerText.includes("Ready for development") || document.body.innerText.includes("Get Dev Mode")')
with sync_playwright() as p:
    b=p.chromium.launch(headless=False)
    ctx=b.new_context(viewport={'width':1600,'height':900})
    ctx.add_cookies(cookies)
    page=ctx.new_page()
    page.goto(f'https://www.figma.com/file/{FK}/Dev-Mode-Test-File',wait_until='domcontentloaded',timeout=60000)
    page.wait_for_timeout(30000)
    print('初始 is_dev:', is_dev(page))
    # 找 Toolbelt Design 的可见元素坐标
    bb=page.evaluate('''() => {
      const els=[...document.querySelectorAll('[class*="toolbelt_mode_segmented_control"] *')];
      const leaf=els.find(e=>e.textContent.trim()==='Design' && e.children.length===0);
      if(!leaf) return null;
      const r=leaf.getBoundingClientRect();
      // 若自身不可见, 向上找可见父级
      let el=leaf;
      for(let i=0;i<5;i++){
        const rr=el.getBoundingClientRect();
        if(rr.width>0&&rr.height>0) return {x:rr.x+rr.width/2,y:rr.y+rr.height/2,w:rr.width,h:rr.height};
        el=el.parentElement;
      }
      return null;
    }''')
    print('Design坐标:', bb)
    if bb:
        page.mouse.click(bb['x'], bb['y'])
        page.wait_for_timeout(8000)
        print('点击后 is_dev:', is_dev(page))
    page.screenshot(path='ui_op3.png')
    b.close()
