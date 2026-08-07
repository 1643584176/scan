"""抓 m.uber.com graphql 请求的完整 headers + cookie"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    captured = {}
    def on_req(r):
        if 'go/graphql' in r.url and 'captured' not in captured:
            captured['headers'] = dict(r.headers)
            captured['url'] = r.url
    page.on('request', on_req)
    page.goto('https://m.uber.com/go/home', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)

    print('=== 真实 graphql 请求 headers ===')
    for k, v in captured.get('headers', {}).items():
        print(f'  {k}: {v[:100]}')
    print()
    print('=== cookies ===')
    for c in ctx.cookies():
        print(f'  {c["name"]}={c["value"][:80]} domain={c["domain"]}')
    print()
    # meta csrf
    meta = page.evaluate("""() => {
        const m = document.querySelector('meta[name=csrf-token], meta[name=csrf], meta[name=_csrf]');
        return m ? m.content : 'NO_META';
    }""")
    print('meta csrf:', meta)
    br.close()
