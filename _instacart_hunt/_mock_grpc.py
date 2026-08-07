"""模拟合法 gRPC-web 空响应修复 hydration，再走注册流程"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()

    def mock_rise(route):
        url = route.request.url
        if 'icprivate.com' in url:
            # grpc-web-text: base64(0x00 flags + 0x00000000 len + empty body)
            route.fulfill(status=200, content_type='application/grpc-web-text', body='AAAAAA==')
        else:
            route.continue_()
    page.route('**/*', mock_rise)

    console_msgs = []
    page.on('console', lambda m: console_msgs.append((m.type, m.text[:160])))
    gql = []
    page.on('request', lambda r: gql.append((r.method, r.url, r.post_data[:2000] if r.post_data else '')) if 'graphql' in r.url else None)

    page.goto('https://www.instacart.com/signup', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(9000)

    # 键盘输入 + Enter
    page.click('input[name=email]')
    page.keyboard.type('test.probe.2026.insta@gmail.com', delay=25)
    page.wait_for_timeout(1000)
    page.keyboard.press('Enter')
    page.wait_for_timeout(8000)

    print('=== console 消息 ===')
    for t, m in console_msgs[:15]:
        print(f'  [{t}] {m}')

    print()
    print('=== graphql 请求 ===')
    seen = set()
    for m, u, b in gql:
        from urllib.parse import urlparse, parse_qs
        op = parse_qs(urlparse(u).query).get('operationName', ['?'])[0]
        if (op, m) in seen:
            continue
        seen.add((op, m))
        print(f'{m} {op}')
        if b:
            print(f'    {b[:300]}')
    br.close()
