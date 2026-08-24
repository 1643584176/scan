# -*- coding: utf-8 -*-
"""匿名打开 A 的 Weave 文件页面——判断文件公开性
- 匿名打开 /make/5zb5YkoxMa09KpqOyuLcHD
- 若公开: 渲染内容/账号选择页(证明公开)
- 若私有: 403/登录墙
对照: A 的私有 design 文件(5Gs4PaTz11Hlk2sqVnidBG) 匿名打开
"""
import io, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_PRIV = "5Gs4PaTz11Hlk2sqVnidBG"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1400, 'height': 900})
    page = ctx.new_page()
    for label, key in [("A的Weave文件", A_MAKE), ("A的私有design", A_PRIV)]:
        try:
            page.goto(BASE + f'/make/{key}', wait_until='domcontentloaded', timeout=45000)
        except Exception as e:
            print(f'[{label}] goto err: {str(e)[:100]}')
        page.wait_for_timeout(10000)
        print(f'\n=== {label} ===')
        print('url:', page.url)
        try:
            t = page.title()
            print('title:', t)
        except Exception:
            pass
        body = page.evaluate("() => document.body.innerText.slice(0, 1200)")
        print('body:', body[:1100])
    b.close()
