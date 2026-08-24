# -*- coding: utf-8 -*-
"""Make 文件视图权限 vs API 权限细节对照
核心问题: B 对 A 的 Weave 文件只有"查看"权限时——
 1. 页面能否正常打开 Weave 编辑器(还是 403/只读提示)
 2. 页面上能否看到 AI 线程/代码内容(增量价值判断)
 3. 抓取页面实际发出的 /api/ai_chat/ 与 make 相关请求(真实契约)
"""
import io, json, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"   # A 的 Weave 文件
B_MAKE = "76rf9byPrduayQieCWJkqV"   # B 自己的 Make(对照)
ROLE = sys.argv[1] if len(sys.argv) > 1 else "B"


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


CK_FILE = 'ws_cookie_B_new.txt' if ROLE == 'B' else 'ws_cookie_A_new.txt'
TARGET = A_MAKE if ROLE == 'B' else B_MAKE
print(f"角色={ROLE} cookie={CK_FILE} 目标Make={TARGET}")

captured = []
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={'width': 1500, 'height': 900})
    ctx.add_cookies(cookies_for_browser(raw_cookie(CK_FILE)))
    page = ctx.new_page()

    def on_request(request):
        url = request.url
        if '/api/' in url and not any(x in url for x in ('.png', '.jpg', '.woff', '.css', 'analytics',
                                                          'metrics', 'session/', 'features', 'team_payments')):
            captured.append({'method': request.method, 'url': url[:260],
                             'body': (request.post_data or '')[:800]})

    def on_response(response):
        url = response.url
        if '/api/ai_chat/' in url or '/api/make/' in url or 'make_versions' in url:
            try:
                body = response.text()[:1500]
            except Exception:
                body = ''
            print(f"\n▶ {response.status} {response.request.method} {url[:200]}")
            print(f"  ↳ {body[:1500]}")

    page.on('request', on_request)
    page.on('response', on_response)
    try:
        page.goto(BASE + f'/make/{TARGET}', wait_until='domcontentloaded', timeout=60000)
    except Exception as e:
        print('goto err:', str(e)[:120])
    page.wait_for_timeout(25000)

    title = page.title()
    print('\n=== 页面状态 ===')
    print('title:', title)
    # 收集页面文本要点
    body_text = page.evaluate("() => document.body.innerText.slice(0, 3000)")
    print('--- body text ---')
    print(body_text[:2500])

    # 统计抓到的 API 调用
    print('\n=== API 请求汇总 ===')
    for c in captured:
        print(f"{c['method']} {c['url']}")
    print(f"\n捕获 {len(captured)} 个请求")
    b.close()
