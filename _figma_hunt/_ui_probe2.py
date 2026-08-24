# -*- coding: utf-8 -*-
# UI DOM 探查2: 提取模式切换/按钮/图层树/发布入口
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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(viewport={"width": 1600, "height": 900},
                              user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    page.goto(f"https://www.figma.com/file/{FK}/Dev-Mode-Test-File", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(25000)

    info = page.evaluate("""() => {
      const out = {buttons: [], labels: [], hasComponent: false, publishVisible: false};
      document.querySelectorAll('button').forEach(b => {
        const t = (b.innerText || '').trim();
        const aria = b.getAttribute('aria-label') || '';
        if (t && t.length < 40) out.buttons.push(t);
        else if (aria && aria.length < 60) out.buttons.push('['+aria+']');
      });
      // 模式标签
      document.querySelectorAll('[role="tab"], [data-testid], [aria-selected]').forEach(e => {
        const t = (e.innerText || '').trim();
        if (t && t.length < 40) out.labels.push(t);
      });
      // 图层树: 找组件标记
      const body = document.body.innerText;
      out.hasComponent = body.includes('Create component');
      out.publishVisible = body.includes('Publish');
      return out;
    }""")
    print(json.dumps(info, ensure_ascii=False)[:3000])
    browser.close()
