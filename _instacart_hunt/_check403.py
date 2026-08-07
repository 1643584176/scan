"""检查 Instacart GraphQL 403 的响应体，判断风控类型"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)  # headed 模式
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()

    def block_rise(route):
        if 'icprivate.com' in route.request.url:
            route.fulfill(status=200, content_type='application/grpc-web-text', body='')
        else:
            route.continue_()
    page.route('**/*', block_rise)

    gql_responses = []
    def on_response(r):
        if 'graphql' in r.url:
            try:
                body = r.text()[:400]
                gql_responses.append((r.status, r.url[:120], body))
            except Exception:
                gql_responses.append((r.status, r.url[:120], 'NO_BODY'))
    page.on('response', on_response)

    page.goto('https://www.instacart.com/signup', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(10000)

    print('=== GraphQL 响应 ===')
    for st, u, b in gql_responses:
        print(f'[{st}] {u}')
        print(f'    {b[:300]}')
        print()

    # 检查风控脚本
    scripts = page.evaluate("""() => [...document.querySelectorAll('script')].map(s => s.src).filter(Boolean)""")
    print('=== 页面脚本 ===')
    for s in scripts[:20]:
        print(' ', s[:120])
    br.close()
