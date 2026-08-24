# -*- coding: utf-8 -*-
"""A 打开 Weave 文件 → Share 弹窗 → Audience 改 Only people → Save
用 locator API 操作, 抓所有非 GET 请求拿到分享保存 API
"""
import io, json, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
KEY = "5zb5YkoxMa09KpqOyuLcHD"


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
    ctx.add_cookies(cookies_for_browser(raw_cookie('ws_cookie_A_new.txt')))
    page = ctx.new_page()

    def on_request(request):
        u = request.url
        if '/api/' in u and request.method != 'GET' and not any(
                x in u for x in ('.png', '.css', '.js', 'sentry', 'metrics', 'statsig', 'figment', 'web_logger')):
            try:
                bd = (request.post_data or '')[:800]
            except Exception:
                bd = '<binary/gzip>'
            captured.append({'m': request.method, 'u': u[:260], 'b': bd})

    page.on('request', on_request)
    page.goto(BASE + f'/make/{KEY}', wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(15000)

    # 点 Share 按钮
    try:
        page.get_by_text("Share", exact=True).first.click(timeout=8000)
        print("clicked Share")
    except Exception as e:
        print("share click fail:", str(e)[:100])
    page.wait_for_timeout(5000)

    # 点 audience 行
    try:
        page.locator('[data-testid="file-audience-row"]').first.click(timeout=8000)
        print("clicked audience row")
    except Exception as e:
        print("audience fail:", str(e)[:100])
    page.wait_for_timeout(3000)

    # 选 Only people
    try:
        page.get_by_text("Only people", exact=False).first.click(timeout=5000)
        print("clicked only people")
    except Exception as e:
        print("only-people fail:", str(e)[:100])
    page.wait_for_timeout(3000)

    # 点 Save
    for label in ["Save", "Done"]:
        try:
            page.get_by_text(label, exact=True).first.click(timeout=3000)
            print(f"clicked {label}")
            break
        except Exception:
            continue
    page.wait_for_timeout(6000)

    print('\n=== WRITE API calls ===')
    for c in captured:
        print(c['m'], c['u'])
        if c['b']:
            print('   body:', c['b'][:600])
    print('total:', len(captured))
    b.close()
