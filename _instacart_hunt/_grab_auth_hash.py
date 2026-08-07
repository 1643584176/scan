"""headed 模式走注册流程，抓认证 mutation 的 APQ hash"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse, parse_qs

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()

    def block_rise(route):
        if 'icprivate.com' in route.request.url:
            route.fulfill(status=200, content_type='application/grpc-web-text', body='')
        else:
            route.continue_()
    page.route('**/*', block_rise)

    gql = []
    def on_req(r):
        if 'graphql' in r.url:
            gql.append((r.method, r.url, r.post_data[:3000] if r.post_data else ''))
    page.on('request', on_req)

    page.goto('https://www.instacart.com/signup', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)

    # 填邮箱
    page.fill('input[name=email]', 'test.probe.2026.insta@gmail.com')
    page.wait_for_timeout(1500)
    # 点 Continue
    page.click('button[type=submit]:has-text("Continue")')
    page.wait_for_timeout(8000)
    print('URL:', page.url)

    # 页面新增文本（下一步是什么：密码？验证码？）
    new_txt = page.evaluate("""() => [...document.querySelectorAll('p, span, label, h1, h2')].filter(e => e.offsetParent !== null && (e.innerText||'').trim().length > 2 && (e.innerText||'').trim().length < 120).map(e => e.innerText.trim().replace(/\\n/g, ' '))""")
    seen_before = {'Log in', 'Continue', 'Enter your email address'}
    print()
    print('=== 提交后页面文本 ===')
    for t in new_txt[:25]:
        if t not in seen_before:
            print(' ', t[:120])

    print()
    print('=== graphql 请求（新） ===')
    seen = set()
    for m, u, b in gql:
        params = parse_qs(urlparse(u).query)
        op = params.get('operationName', ['?'])[0]
        if (op, m) in seen:
            continue
        seen.add((op, m))
        ext = params.get('extensions', [''])[0]
        try:
            h = json.loads(ext).get('persistedQuery', {}).get('sha256Hash', '')[:24]
        except Exception:
            h = ''
        print(f'{m} {op} hash={h}')
        if b and m == 'POST':
            print(f'    POST: {b[:300]}')
    br.close()
