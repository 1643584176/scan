"""抓 www.uber.com /api/* POST 的完整 body + 响应，复现未认证面"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

posts = []
with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()

    def on_req(req):
        u = req.url
        if req.method == 'POST' and '/api/' in u:
            try:
                body = req.post_data or ''
            except Exception:
                body = ''
            posts.append({'url': u, 'headers': dict(req.headers), 'body': body[:800]})

    page.on('request', on_req)
    page.goto('https://www.uber.com/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(10000)
    cookies = ctx.cookies()
    br.close()

print(f'共 {len(posts)} 个 POST:')
seen = set()
for p_ in posts:
    u = p_['url']
    print(f'\n=== {u} ===')
    h = {k: v for k, v in p_['headers'].items() if k in ('content-type', 'x-csrf-token', 'x-uber-client-name', 'apollographql-client-name')}
    print(f'    headers: {h}')
    print(f'    body: {p_["body"][:500]}')

# 保存 cookies 供复现
with open('_uber_www_cookies.json', 'w', encoding='utf-8') as f:
    json.dump([{'name': c['name'], 'value': c['value']} for c in cookies], f)
print('\ncookies 已保存 _uber_www_cookies.json')
