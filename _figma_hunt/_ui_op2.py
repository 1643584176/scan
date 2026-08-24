# -*- coding: utf-8 -*-
# 自主操作v2: Toolbelt Design -> Layers面板 -> 选节点 -> Ctrl+Alt+K -> 验证组件
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
          const out={layers:'',sel:''};
          document.querySelectorAll('[aria-label="Layers"],[data-testid*="layers"],[data-testid*="Layers"]').forEach(e=>{ if(e.innerText) out.layers=e.innerText.slice(0,700); });
          const sel=document.querySelector('[data-testid="selection-names"], [aria-label*="Selection"]');
          if(sel) out.sel=sel.innerText.slice(0,100);
          return out;
        }""")
        print(f"[{tag}] layers={info['layers'][:500]}")
        print(f"[{tag}] sel={info['sel'][:100]}")
    except Exception as e:
        print(f"[{tag}] dump err: {str(e)[:80]}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(viewport={"width": 1600, "height": 900})
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto(f"https://www.figma.com/file/{FK}/Dev-Mode-Test-File", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(30000)

    # 1) 点 Toolbelt Design
    try:
        page.locator('label:has-text("Design")').first.click()
        print("-> 已点击 Toolbelt Design")
    except Exception as e:
        print("!! Design点击失败:", str(e)[:100])
    page.wait_for_timeout(12000)
    dump(page, "design-mode")

    # 2) 打开 Layers 面板(按钮文本 Layers)
    try:
        page.get_by_role("button", name="Layers").first.click()
        print("-> 已点击 Layers 按钮")
    except Exception as e:
        print("!! Layers按钮失败:", str(e)[:100])
    page.wait_for_timeout(6000)
    dump(page, "layers-open")
    page.screenshot(path="ui_design2.png")
    browser.close()
