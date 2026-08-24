# -*- coding: utf-8 -*-
# UI 探查: A cookie 打开文件页, 截图+提取当前模式/组件/发布按钮状态
import io, sys, json, re
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
    try:
        page.goto(f"https://www.figma.com/file/{FK}/Dev-Mode-Test-File", wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print("goto err:", str(e)[:150])
    page.wait_for_timeout(20000)  # WAF + 应用加载

    title = page.title()
    print("TITLE:", title)
    try:
        body = page.inner_text("body")
        print("BODY len:", len(body))
        print(body[:800])
    except Exception as e:
        print("body err:", str(e)[:100])

    page.screenshot(path="ui_probe.png")
    print("saved ui_probe.png")
    browser.close()
