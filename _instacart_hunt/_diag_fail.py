"""修复第三方资源加载失败，让 Instacart 页面 JS 正常 hydration，走注册流程抓 APQ hash"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

FAILED = {}

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=True)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()

    # 记录失败请求的域名
    def on_fail(r):
        host = r.url.split('/')[2] if '//' in r.url else '?'
        FAILED[host] = FAILED.get(host, 0) + 1
        print(f'[FAIL] {r.url[:100]}')
    page.on('requestfailed', on_fail)
    page.on('response', lambda r: print(f'[HTTP {r.status}] {r.url[:100]}') if r.status >= 400 else None)

    console_errors = []
    page.on('console', lambda m: console_errors.append(m.text[:150]) if m.type == 'error' else None)

    page.goto('https://www.instacart.com/signup', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(12000)

    print()
    print('=== 失败域名统计 ===')
    for h, c in sorted(FAILED.items(), key=lambda x: -x[1]):
        print(f'  {c}x {h}')
    print()
    print('=== console errors ===')
    for e in console_errors[:10]:
        print(' ', e)
    br.close()
