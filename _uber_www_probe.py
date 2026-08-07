"""抓 www.uber.com 网络请求：找 GraphQL 端点 + 下载 JS"""
import sys, json, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

reqs = []
js_urls = []
with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()

    def on_req(req):
        u = req.url
        if 'graphql' in u or ('/api/' in u):
            reqs.append((u, req.method, dict(req.headers)))
        if '.js' in u and 'uber.com' in u:
            js_urls.append(u)

    page.on('request', on_req)
    try:
        page.goto('https://www.uber.com/', timeout=60000, wait_until='domcontentloaded')
        page.wait_for_timeout(8000)
        print('标题:', page.title())
        print('URL:', page.url)
    except Exception as e:
        print('导航异常:', str(e)[:200])
    cookies = ctx.cookies()
    br.close()

print(f'\n共抓到 {len(reqs)} 个 API 请求:')
for u, m, h in reqs[:30]:
    print(f'\n{m} {u[:250]}')
    interesting = {k: v for k, v in h.items() if k in ('x-csrf-token', 'x-uber-client-name', 'authorization', 'content-type')}
    if interesting:
        print(f'    {interesting}')

print(f'\nJS 文件 {len(js_urls)} 个:')
for u in js_urls[:10]:
    print('   ', u[:200])
