# -*- coding: utf-8 -*-
"""私有化后 B 打开页面——抓全部请求与状态码
关键: B 页面渲染出了 AI 聊天内容,但 API 403。数据从哪来?
"""
import io, json, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
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

log = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1500, 'height': 900})
    ctx.add_cookies(cookies)
    page = ctx.new_page()

    def on_response(response):
        url = response.url
        if '/api/' in url:
            try:
                body = response.text()[:200]
            except Exception:
                body = ''
            log.append({'s': response.status, 'm': response.request.method, 'u': url[:230], 'b': body})

    page.on('response', on_response)
    try:
        page.goto(BASE + f'/make/{A_MAKE}', wait_until='domcontentloaded', timeout=45000)
    except Exception as e:
        print('goto err:', str(e)[:100])
    page.wait_for_timeout(15000)

    print('=== url:', page.url)
    print('=== title:', page.title())
    for item in log:
        print(f"{item['s']} {item['m']} {item['u']}")
        if item['s'] == 200 and any(x in item['u'] for x in ('realtime', 'ai_chat', 'message', 'thread', 'make', 'meta')):
            print(f"   ↳ {item['b'][:300]}")
    print(f"\n共 {len(log)} 个 API 请求")
    b.close()
