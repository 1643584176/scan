"""m.uber.com 同源 GraphQL 验证 + 抓真实请求格式"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    gql_reqs = []
    def on_req(r):
        if 'graphql' in r.url:
            gql_reqs.append((r.method, r.url, r.post_data[:4000] if r.post_data else '', dict(r.headers)))
    page.on('request', on_req)

    page.goto('https://m.uber.com/go/home', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)

    # 同源 fetch 测试
    result = page.evaluate("""async () => {
        try {
            const r = await fetch('/graphql', {method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({query: '{__typename}'})});
            return r.status + ' | ' + (await r.text()).slice(0, 300);
        } catch(e) { return 'ERR ' + e.message; }
    }""")
    print('=== 同源 fetch /graphql ===')
    print(result)
    print()

    # 抓页面真实 graphql 请求
    print('=== 页面真实 graphql 请求 ===')
    seen = set()
    for m, u, b, hd in gql_reqs[:10]:
        key = (m, u.split('?')[0])
        if key in seen:
            continue
        seen.add(key)
        print(f'{m} {u[:120]}')
        if b:
            print(f'    body: {b[:600]}')
    br.close()
