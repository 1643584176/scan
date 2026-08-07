"""抓 apps.uber.com 的网络请求：找 GraphQL 端点 + headers + cookies"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

reqs = []
with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()

    def on_req(req):
        u = req.url
        if any(k in u for k in ['graphql', 'gql', 'api', 'rpc', 'rest']):
            reqs.append((u, req.method, dict(req.headers)))

    page.on('request', on_req)
    page.goto('https://apps.uber.com/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    cookies = ctx.cookies()
    br.close()

print(f'共抓到 {len(reqs)} 个 API 请求:')
for u, m, h in reqs[:25]:
    print(f'\n{m} {u[:200]}')
    interesting = {k: v for k, v in h.items() if k in ('x-csrf-token', 'x-uber-client-name', 'authorization', 'content-type', 'apollographql-client-name')}
    if interesting:
        print(f'    {interesting}')
