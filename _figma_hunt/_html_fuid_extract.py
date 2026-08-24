# -*- coding: utf-8 -*-
"""匿名打开 Make 文件 → 提取 HTML 中的 fuid(owner 标识)"""
import io, re, sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
KEY = "5zb5YkoxMa09KpqOyuLcHD"
A_UID = "1666382703778278399"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1400, 'height': 900})
    page = ctx.new_page()
    html = ''

    def on_resp(r):
        global html
        if 'text/html' in (r.headers.get('content-type') or '') and 'figma.com' in r.url:
            try:
                html = r.text()[:200000]
            except Exception:
                pass

    page.on('response', on_resp)
    page.goto(BASE + '/make/' + KEY, wait_until='domcontentloaded', timeout=45000)
    page.wait_for_timeout(6000)

    print('html len:', len(html))
    fuids = set(re.findall(r'fuid[\s=:&"\'/\\]+(\d{10,20})', html))
    print('fuid 引用:', fuids)
    print('A uid in html:', A_UID in html)
    for pat in [r'/api/user/state[^"\'<]*', r'/api/session/state[^"\'<]*', r'fuid[^"\'<,}]{0,60}']:
        hits = re.findall(pat, html)[:4]
        for h in hits:
            print('hit:', h[:140])
    b.close()
