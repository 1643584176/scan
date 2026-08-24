# -*- coding: utf-8 -*-
"""B 登录打开 Make 文件 → 抓 SSR HTML 看 fuid 来源"""
import io, re, sys
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
KEY = "5zb5YkoxMa09KpqOyuLcHD"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"

raw = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
cookies = []
for pair in raw.split('; '):
    if '=' not in pair:
        continue
    n, v = pair.split('=', 1)
    c = {'name': n, 'value': v, 'secure': True, 'sameSite': 'Lax'}
    if n.startswith('__Host-'):
        c['url'] = BASE
    else:
        c.update({'domain': '.figma.com', 'path': '/'})
    cookies.append(c)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1400, 'height': 900})
    ctx.add_cookies(cookies)
    page = ctx.new_page()
    html = ''

    def on_resp(r):
        global html
        if 'text/html' in (r.headers.get('content-type') or '') and 'figma.com' in r.url:
            try:
                html = r.text()[:500000]
            except Exception:
                pass

    page.on('response', on_resp)
    page.goto(BASE + '/make/' + KEY, wait_until='domcontentloaded', timeout=45000)
    page.wait_for_timeout(8000)

    print('html len:', len(html))
    print('A uid in html:', A_UID in html)
    print('B uid in html:', B_UID in html)
    for pat in [r'/api/user/state[^"\'<]{0,120}', r'/api/session/state[^"\'<]{0,120}',
                r'fuid[\s=:&"\'/\\]+(\d{10,20})', r'team_id[^"\'<,}]{0,60}']:
        hits = set(re.findall(pat, html))
        print(f'--- {pat[:30]}: {list(hits)[:5]}')
    # 找 config JSON 片段
    m = re.search(r'fuid.{0,200}', html)
    if m:
        print('fuid context:', m.group(0)[:250])
    b.close()
