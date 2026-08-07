"""抓 auth.uber.com/v2：JS chunk + 真实 API 请求（认证链确定性侦察）"""
import sys, json
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
        if req.method == 'POST' and ('auth.uber.com' in u or 'login' in u.lower() or 'signup' in u.lower()):
            try:
                reqs.append({'url': u, 'headers': dict(req.headers),
                             'body': (req.post_data or '')[:1500]})
            except Exception:
                pass
        if '.js' in u and 'uber.com' in u:
            js_urls.append(u)

    page.on('request', on_req)
    page.goto('https://auth.uber.com/v2/', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    print('标题:', page.title())
    print('URL:', page.url)
    # 截个图看登录页形态
    page.screenshot(path='_uber_auth_page.png')
    br.close()

print(f'\n=== POST 请求: {len(reqs)} ===')
for r_ in reqs[:20]:
    print(f'\n{r_["url"][:160]}')
    h = {k: v for k, v in r_['headers'].items() if k in ('content-type', 'x-csrf-token', 'x-uber-client-name')}
    print(f'  headers: {h}')
    print(f'  body: {r_["body"][:500]}')

print(f'\n=== JS chunk: {len(js_urls)} ===')
for u in list(dict.fromkeys(js_urls))[:40]:
    print(' ', u[:150])
