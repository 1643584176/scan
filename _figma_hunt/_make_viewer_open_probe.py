# -*- coding: utf-8 -*-
"""B 以 Viewer 身份打开 A 的 Weave 文件——选择账号后实际体验
目标: B(viewer) 能否打开编辑器? 能否看到 AI 线程/代码? 发出哪些请求?
"""
import io, json, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"


def raw_cookie(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


def cookies_for_browser(raw):
    result = []
    for pair in raw.split('; '):
        if '=' not in pair:
            continue
        name, value = pair.split('=', 1)
        item = {'name': name, 'value': value, 'secure': True, 'sameSite': 'Lax'}
        if name.startswith('__Host-'):
            item['url'] = BASE
        else:
            item.update({'domain': '.figma.com', 'path': '/'})
        result.append(item)
    return result


captured = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1500, 'height': 900})
    ctx.add_cookies(cookies_for_browser(raw_cookie('ws_cookie_B_new.txt')))
    page = ctx.new_page()

    def on_response(response):
        url = response.url
        if '/api/' in url and 'ai_chat' in url:
            try:
                body = response.text()[:1200]
            except Exception:
                body = ''
            print(f"\n▶ {response.status} {response.request.method} {url[:220]}")
            print(f"  ↳ {body[:1200]}")

    def on_request(request):
        url = request.url
        if '/api/' in url and ('ai_chat' in url or 'make' in url) and not any(x in url for x in ('.png', '.woff', '.css')):
            captured.append({'method': request.method, 'url': url[:240],
                             'body': (request.post_data or '')[:600]})

    page.on('response', on_response)
    page.on('request', on_request)
    try:
        page.goto(BASE + f'/make/{A_MAKE}', wait_until='domcontentloaded', timeout=60000)
    except Exception as e:
        print('goto err:', str(e)[:120])
    page.wait_for_timeout(8000)

    # 选择 B 账号 (Viewer on file)
    try:
        b_btn = page.get_by_text("boboli", exact=True)
        print('b_btn count:', b_btn.count())
        b_btn.first.click()
        print('clicked B account')
    except Exception as e:
        print('click B fail:', str(e)[:150])
    page.wait_for_timeout(18000)

    print('\n=== URL:', page.url)
    print('=== title:', page.title())
    body_text = page.evaluate("() => document.body.innerText.slice(0, 4000)")
    print('--- body text ---')
    print(body_text[:3500])

    print('\n=== ai_chat/make 请求 ===')
    for c in captured:
        print(f"{c['method']} {c['url']}")
    print(f"\n捕获 {len(captured)} 个")
    b.close()
