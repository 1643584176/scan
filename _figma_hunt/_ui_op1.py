# -*- coding: utf-8 -*-
# 自主操作: 切Design模式 -> Layers面板选中元素 -> Ctrl+Alt+K创建组件 -> 检查
import io, sys, json
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FK = "bv2nMIdFf4u3dESGail4sm"
raw = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
pairs = [p.split('=', 1) for p in raw.split('; ') if '=' in p]
cookies = []
for k, v in pairs:
    c = {"name": k, "value": v, "path": "/", "secure": True, "sameSite": "Lax"}
    if not k.startswith('__Host-'):
        c["domain"] = ".figma.com"
    else:
        c["url"] = "https://www.figma.com"
        del c["path"]
    cookies.append(c)

def dump(page, tag):
    try:
        info = page.evaluate("""() => {
          const out={buttons:[],layers:'',body:''};
          document.querySelectorAll('button').forEach(b=>{
            const t=(b.innerText||'').trim(); const al=b.getAttribute('aria-label')||'';
            if(t&&t.length<30) out.buttons.push(t); else if(al&&al.length<50) out.buttons.push('['+al+']');
          });
          const lp=document.querySelector('[aria-label="Layers"]')||document.querySelector('[data-testid="layers-panel"]');
          if(lp) out.layers=lp.innerText.slice(0,600);
          out.body=document.body.innerText.slice(0,400);
          return out;
        }""")
        print(f"[{tag}] buttons={json.dumps(info['buttons'],ensure_ascii=False)[:300]}")
        print(f"[{tag}] layers={info['layers'][:400]}")
        print(f"[{tag}] body={info['body'][:200]}")
    except Exception as e:
        print(f"[{tag}] dump err: {str(e)[:100]}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto(f"https://www.figma.com/file/{FK}/Dev-Mode-Test-File", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(25000)
    dump(page, "loaded")

    # 1) 点 Toolbelt Design(底部, 文本恰为 Design 的按钮)
    clicked = False
    for sel in ['button:has-text("Design")', 'div[role="button"]:has-text("Design")']:
        loc = page.locator(sel)
        n = loc.count()
        print(f"  Design候选 {sel}: {n}个")
        for i in range(min(n, 5)):
            t = loc.nth(i).inner_text().strip()
            if t == "Design":
                loc.nth(i).click()
                clicked = True
                print("  -> 点击了 Design")
                break
        if clicked:
            break
    if not clicked:
        print("  !! 未找到独立 Design 按钮")
    page.wait_for_timeout(8000)
    dump(page, "after-design")
    page.screenshot(path="ui_design.png")
    browser.close()
