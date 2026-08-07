"""确定性侦察：找 getPesData 的真实调用页面，抓请求 body + JS chunk"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

pes_reqs = []
js_urls = []
with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()

    def on_req(req):
        u = req.url
        if 'getPesData' in u or ('/api/' in u and 'pes' in u.lower()):
            try:
                pes_reqs.append({'url': u, 'method': req.method,
                                 'headers': dict(req.headers), 'body': (req.post_data or '')[:2000]})
            except Exception:
                pass
        if '.js' in u and 'uber.com' in u:
            js_urls.append(u)

    page.on('request', on_req)
    # 司机收入相关页面
    for path in ['https://www.uber.com/drive/earnings/', 'https://www.uber.com/drive/']:
        try:
            print(f'访问 {path} ...')
            page.goto(path, timeout=45000, wait_until='domcontentloaded')
            page.wait_for_timeout(6000)
            print(f'  标题: {page.title()[:60]}  URL: {page.url[:80]}')
        except Exception as e:
            print(f'  异常: {str(e)[:120]}')
    br.close()

print(f'\n=== getPesData 相关请求: {len(pes_reqs)} ===')
for r_ in pes_reqs:
    print(f'\n{m_ if False else r_["method"]} {r_["url"][:150]}')
    print(f'  body: {r_["body"][:800]}')

print(f'\n=== JS chunk: {len(js_urls)} ===')
for u in list(dict.fromkeys(js_urls))[:30]:
    print(' ', u[:140])
