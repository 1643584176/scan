# -*- coding: utf-8 -*-
"""走通 checkout 流程：加购→篡改价格→到支付页，截图金额"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

OUT = 'D:/scan/_wolt_hunt/_payment_flow.jsonl'
open(OUT, 'w').close()
SHOT = 'D:/scan/_wolt_hunt/_payment_shots'
os.makedirs(SHOT, exist_ok=True)

REQS = []

def hook(route):
    req = route.request
    if req.resource_type in ('xhr', 'fetch'):
        entry = {'m': req.method, 'u': req.url, 'post': (req.post_data or '')[:2000]}
        REQS.append(entry)
        with open(OUT, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        # 拦截 checkout 请求，篡改价格
        if 'pages/checkout' in req.url and req.method == 'POST':
            try:
                body = json.loads(req.post_data)
                items = body.get('purchase_plan', {}).get('menu_items', [])
                if items:
                    for it in items:
                        ori = it.get('price', 0)
                        it['price'] = 1       # 篡改为 1 cent
                        it['base_price'] = 1
                        it['end_amount'] = 1
                    print(f'[HACK] checkout body intercepted: price {ori} -> 1')
                route.continue_(post_data=json.dumps(body, ensure_ascii=False))
                return
            except Exception as e:
                print(f'[HACK] error: {e}')
    route.continue_()

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server'])
    ctx = b.new_context(viewport={'width': 1440, 'height': 900}, locale='en-US')
    page = ctx.new_page()
    page.route('**/*', hook)
    
    page.goto('https://wolt.com/en/fin/helsinki/venue/wolt-market-kamppi', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(8000)
    page.screenshot(path=f'{SHOT}/01_venue.png')
    
    # GDPR
    try: page.locator('[data-test-id="decline-button"]').click(timeout=3000)
    except: pass
    page.wait_for_timeout(1000)
    
    # 地址选择
    try:
        addr_btn = page.locator('[data-test-id*="Delivery" i], [data-test-id*="address" i], [data-test-id*="statusButton" i]').first
        addr_btn.click(timeout=5000)
        page.wait_for_timeout(3000)
        page.screenshot(path=f'{SHOT}/02_addr_dialog.png')
        # 选 radio (Helsinki)
        try:
            page.locator('[role="dialog"] [role="radio"]').first.click(timeout=3000)
            page.wait_for_timeout(500)
        except: pass
        # 点 Done
        try:
            page.locator('[role="dialog"] button:has-text("Done")').click(timeout=3000)
            page.wait_for_timeout(6000)
        except: pass
    except Exception as e:
        print(f'addr dialog fail: {str(e)[:100]}')
    page.screenshot(path=f'{SHOT}/03_after_addr.png')
    
    # 加商品
    add_btns = page.locator('button:has-text("Add"), [aria-label*="add" i], [data-test-id*="add" i]')
    n = add_btns.count()
    print(f'add buttons: {n}')
    for i in range(min(n, 5)):
        try:
            btn = add_btns.nth(i)
            btn.scroll_into_view_if_needed(timeout=3000)
            btn.click(timeout=5000)
            print(f'clicked add #{i}')
            page.wait_for_timeout(3000)
            break
        except Exception as e:
            print(f'add #{i} fail: {str(e)[:80]}')
    page.screenshot(path=f'{SHOT}/04_after_add.png')
    
    # 去购物车/checkout
    for sel in ['[data-test-id*="cart" i]', '[data-test-id*="basket" i]', 'a[href*="checkout"]', 'button:has-text("View cart")']:
        try:
            page.locator(sel).first.click(timeout=3000)
            print(f'clicked {sel}')
            break
        except: pass
    page.wait_for_timeout(8000)  # 等待 checkout 请求完成
    page.screenshot(path=f'{SHOT}/05_checkout.png')
    
    # 继续走 checkout → 支付：填地址(如果需要)、选配送
    # 看页面当前的 URL 和内容
    print(f'URL: {page.url[:120]}')
    
    # 找 "Continue" / "Proceed" / "Place order" 按钮
    btns_text = page.evaluate("""() => [...document.querySelectorAll('button')].map(b => b.textContent.trim()).filter(Boolean).slice(0,20)""")
    print('buttons:', btns_text)
    
    # 如果有地址输入框，填地址
    try:
        addr_input = page.locator('input[data-test-id*="address" i], input[placeholder*="address" i], input[placeholder*="street" i]').first
        addr_input.fill('Mannerheimintie 1, Helsinki', timeout=5000)
        page.wait_for_timeout(2000)
        # 选第一个自动补全
        try:
            page.locator('[role="option"]').first.click(timeout=3000)
        except: pass
        page.wait_for_timeout(2000)
        page.screenshot(path=f'{SHOT}/06_addr_filled.png')
    except Exception as e:
        print(f'addr fill fail: {str(e)[:100]}')
    
    # 再截一次，看是否能到支付页
    page.wait_for_timeout(5000)
    page.screenshot(path=f'{SHOT}/07_payment_or_block.png')
    btns_text2 = page.evaluate("""() => [...document.querySelectorAll('button, [role="button"]')].map(b => b.textContent.trim()).filter(Boolean).slice(0,25)""")
    print('buttons2:', btns_text2)
    print(f'URL2: {page.url[:150]}')
    b.close()

print(f'DONE: {len(REQS)} requests')
