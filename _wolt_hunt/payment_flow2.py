# -*- coding: utf-8 -*-
"""方案B：用 localStorage 预设地址，直接到 checkout URL"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

SHOT = 'D:/scan/_wolt_hunt/_payment_shots'
os.makedirs(SHOT, exist_ok=True)
OUT = 'D:/scan/_wolt_hunt/_payment_flow.jsonl'
open(OUT, 'w').close()
REQS = []

def hook(route):
    req = route.request
    if req.resource_type in ('xhr', 'fetch'):
        entry = {'m': req.method, 'u': req.url, 'post': (req.post_data or '')[:2000]}
        REQS.append(entry)
        with open(OUT, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        # 拦截 checkout，篡改价格
        if 'pages/checkout' in req.url and req.method == 'POST':
            try:
                body = json.loads(req.post_data)
                items = body.get('purchase_plan', {}).get('menu_items', [])
                if items:
                    for it in items:
                        ori = it.get('price', 0)
                        it['price'] = 1
                        it['base_price'] = 1
                        it['end_amount'] = 1
                    print(f'[HACK] price {ori} -> 1')
                route.continue_(post_data=json.dumps(body, ensure_ascii=False))
                return
            except Exception as e:
                print(f'[HACK] err: {e}')
    route.continue_()

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, locale='en-US')
    page = ctx.new_page()
    page.route('**/*', hook)
    
    # 步骤1: 到venue页，先处理地址dialog
    page.goto('https://wolt.com/en/fin/helsinki/venue/wolt-market-kamppi', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    try: page.locator('[data-test-id="decline-button"]').click(timeout=3000)
    except: pass
    page.wait_for_timeout(1000)
    page.screenshot(path=f'{SHOT}/_01_venue.png')
    
    # 点"Choose location"按钮
    for sel in ['text=Choose location', 'button:has-text("Choose")', '[data-test-id*="DeliveryUnavailable"]']:
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible():
                el.click(timeout=3000)
                print(f'clicked: {sel}')
                break
        except: pass
    page.wait_for_timeout(3000)
    page.screenshot(path=f'{SHOT}/_02_dlg_open.png')
    
    # dialog交互
    dlg = page.locator('[role="dialog"]')
    if dlg.count() and dlg.is_visible():
        print('dialog visible')
        # 选Delivery radio
        for sel in ['[role="radio"]:has-text("Delivery")', 'label:has-text("Delivery")', 'text=Delivery']:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    el.click(timeout=2000)
                    print(f'clicked delivery: {sel}')
                    break
            except: pass
        page.wait_for_timeout(500)
        # 点Done
        for sel in ['button:has-text("Done")', '[data-test-id*="done"]', 'text=Done']:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    el.click(timeout=3000)
                    print(f'clicked Done: {sel}')
                    break
            except: pass
    else:
        print('NO dialog')
    
    page.wait_for_timeout(8000)
    page.screenshot(path=f'{SHOT}/_03_after_dlg.png')
    
    # 检查是否还有 choose location 按钮
    cl = page.locator('text=Choose location, button:has-text("Choose")')
    has_cl = cl.count() > 0 and cl.first.is_visible()
    print(f'Choose location visible: {has_cl}')
    
    # 不管状态，尝试加商品
    for i in range(3):
        try:
            btn = page.locator('button:has-text("Add"), [data-test-id*="add-item"]').first
            btn.scroll_into_view_if_needed(timeout=3000)
            btn.click(timeout=6000)
            print(f'add clicked')
            page.wait_for_timeout(3000)
            break
        except Exception as e:
            print(f'add fail: {str(e)[:80]}')
    
    # 尝试去cart/checkout URL
    page.goto('https://wolt.com/en/fin/helsinki/checkout', timeout=30000, wait_until='domcontentloaded')
    page.wait_for_timeout(10000)
    page.screenshot(path=f'{SHOT}/_04_checkout_page.png')
    print(f'URL: {page.url[:150]}')
    btns = page.evaluate("""() => [...document.querySelectorAll('button')].map(b => b.textContent.trim()).filter(Boolean).slice(0,20)""")
    print('btns:', btns)
    
    b.close()
print(f'DONE: {len(REQS)} requests')
for r in REQS:
    if any(k in r['u'] for k in ('checkout', 'basket', 'cart', 'order-xp')):
        print(f'  {r["m"]} {r["u"][:150]}')
        if r.get('post'):
            print(f'    body: {r["post"][:300]}')
