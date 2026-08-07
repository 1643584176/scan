"""修复 React 受控输入：用键盘输入 + 检查 value + 观察按钮状态"""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

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
    page.on('request', lambda r: gql.append((r.method, r.url, r.post_data[:2000] if r.post_data else '')) if 'graphql' in r.url else None)

    page.goto('https://www.instacart.com/signup', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)

    # 点击输入框后用键盘输入（触发 React onChange）
    page.click('input[name=email]')
    page.keyboard.type('test.probe.2026.insta@gmail.com', delay=30)
    page.wait_for_timeout(1500)

    # 检查 value
    val = page.evaluate("() => document.querySelector('input[name=email]').value")
    print('input value:', val)

    # 检查按钮 disabled 状态
    disabled = page.evaluate("() => { const b = [...document.querySelectorAll('button')].find(x => (x.innerText||'').trim()==='Continue'); return b ? b.disabled : 'NO'; }")
    print('按钮 disabled:', disabled)

    # 按 Enter 提交
    page.keyboard.press('Enter')
    page.wait_for_timeout(8000)

    # 页面新文本
    new_txt = page.evaluate("""() => [...document.querySelectorAll('p, span, label, h1, h2')].filter(e => e.offsetParent !== null && (e.innerText||'').trim().length > 2 && (e.innerText||'').trim().length < 120).map(e => e.innerText.trim().replace(/\\n/g, ' '))""")
    print()
    print('=== 提交后页面文本 ===')
    for t in new_txt[:20]:
        print(' ', t[:120])

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
