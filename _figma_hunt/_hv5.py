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
hits=[]
def on_resp(resp):
    u=resp.url
    if any(x in u for x in ('mcp','token_exchange','session')):
        hits.append({'url':u[:180], 'status':resp.status})
with sync_playwright() as p:
    b=p.chromium.launch(headless=False)
    ctx=b.new_context(viewport={'width':1600,'height':900})
    ctx.add_cookies(cookies)
    page=ctx.new_page()
    page.on('response', on_resp)
    page.goto(f'https://www.figma.com/file/{FK}/Dev-Mode-Test-File', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(30000)
    # 找 MCP/AI agent 按钮
    found=page.evaluate('''() => {
      const out=[];
      document.querySelectorAll('button,[role="button"],a').forEach(e=>{
        const t=(e.innerText||'').trim(); const al=e.getAttribute('aria-label')||'';
        if(/mcp|ai agent|connect/i.test(t+' '+al) && t.length<80) out.push((t||al).slice(0,60));
      });
      return out;
    }''')
    print('MCP按钮:', json.dumps(found[:8],ensure_ascii=False))
    # 点击 Connect to AI agent
    for txt in ['Connect to AI agent','Connect to AI agent (MCP)']:
        try:
            page.get_by_text(txt, exact=False).first.click(timeout=4000)
            print('-> 点击:', txt)
            break
        except Exception:
            continue
    page.wait_for_timeout(10000)
    print('HITS:', len(hits))
    for h in hits[:12]: print(' ', h['status'], h['url'])
    page.screenshot(path='hv_mcp.png')
    b.close()
