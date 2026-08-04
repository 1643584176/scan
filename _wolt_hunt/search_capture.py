# -*- coding: utf-8 -*-
"""搜索抓包：在 venue 页触发搜索，抓取搜索 API 端点"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

OUT = 'D:/scan/_wolt_hunt/_search_requests.jsonl'
open(OUT, 'w').close()

REQS = []
def hook(route):
    req = route.request
    if req.resource_type in ('xhr', 'fetch'):
        entry = {'ts': len(REQS), 'm': req.method, 'u': req.url, 'post': (req.post_data or '')[:2000]}
        REQS.append(entry)
        with open(OUT, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    route.continue_()

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, locale='en-US')
    page = ctx.new_page()
    page.route('**/*', hook)
    page.goto('https://wolt.com/en/fin/helsinki/venue/wolt-market-kamppi', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(7000)
    # GDPR
    try:
        page.locator('[data-test-id="decline-button"]').click(timeout=3000)
    except Exception:
        pass
    page.wait_for_timeout(1000)
    # 搜索框
    sbox = page.locator('[data-test-id="menu-search-input"]')
    sbox.click(timeout=5000)
    page.wait_for_timeout(500)
    sbox.fill('pizza', timeout=5000)
    page.wait_for_timeout(3000)
    sbox.press('Enter', timeout=3000)
    page.wait_for_timeout(5000)
    page.screenshot(path='D:/scan/_wolt_hunt/_search_result.png')
    b.close()

# 过滤 API 端点
with open(OUT, encoding='utf-8') as f:
    lines = [json.loads(l) for l in f if l.strip()]
apis = [e for e in lines if any(k in e['u'] for k in ('consumer-api', 'restaurant-api', 'order-xp', 'api'))]
summary = []
for e in apis:
    u = e['u']
    summary.append(f"{e['m']:4s} {u[:180]}")
open('D:/scan/_wolt_hunt/_search_api_summary.txt', 'w', encoding='utf-8').write('\n'.join(summary))
print(f'DONE: {len(lines)} total requests, {len(apis)} API requests')
