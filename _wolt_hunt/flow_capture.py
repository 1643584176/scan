# -*- coding: utf-8 -*-
"""动态抓包：走 venue->加购->checkout 流程，记录所有 XHR/fetch 请求（URL+POST body）"""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

OUT = 'D:/scan/_wolt_hunt/_flow_requests.jsonl'
SHOT = 'D:/scan/_wolt_hunt/_shots'
os.makedirs(SHOT, exist_ok=True)
open(OUT, 'w', encoding='utf-8').close()

REQS = []
def hook(route):
    try:
        req = route.request
        if req.resource_type in ('xhr', 'fetch'):
            entry = {
                'ts': len(REQS),
                'm': req.method,
                'u': req.url,
                'post': (req.post_data or '')[:2000],
            }
            REQS.append(entry)
            with open(OUT, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass
    route.continue_()

def dump(page, name):
    page.screenshot(path=f'{SHOT}/{name}.png')
    print(f'[shot] {name}')

with sync_playwright() as p:
    b = p.chromium.launch(channel='msedge', headless=True, args=['--no-proxy-server'])
    ctx = b.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        locale='en-US', viewport={'width': 1440, 'height': 900})
    page = ctx.new_page()
    page.route('**/*', hook)
    try:
        page.goto('https://wolt.com/en/fin/helsinki/venue/wolt-market-kamppi', timeout=60000, wait_until='domcontentloaded')
        page.wait_for_timeout(8000)
        dump(page, '01_venue')

        # GDPR
        for sel in ['[data-test-id="decline-button"]', 'text=Decline', 'button:has-text("Decline")']:
            try:
                page.locator(sel).first.click(timeout=3000)
                print('[gdpr] declined via', sel)
                break
            except Exception:
                pass
        page.wait_for_timeout(1500)
        dump(page, '02_after_gdpr')

        # 找商品添加按钮
        adders = page.locator('[data-test-id*="add-item"], [data-test-id="ProductCardAddButton"], [aria-label*="Add"], button:has-text("Add")')
        n = adders.count()
        print('[adders] count =', n)
        for i in range(min(n, 5)):
            try:
                adders.nth(i).click(timeout=3000)
                print(f'[add] clicked #{i}')
                page.wait_for_timeout(2000)
                break
            except Exception as e:
                print(f'[add] #{i} fail {e}')

        # 等待购物车请求出现
        page.wait_for_timeout(4000)
        dump(page, '03_after_add')

        # 点购物车 / 去结算
        for sel in ['[data-test-id="cart-button"]', '[data-test-id="CartButton"]', 'a[href*="checkout"]', 'button:has-text("Checkout")', 'button:has-text("View cart")']:
            try:
                page.locator(sel).first.click(timeout=2500)
                print('[nav] clicked', sel)
                break
            except Exception:
                pass
        page.wait_for_timeout(6000)
        dump(page, '04_checkout')

        # 尝试填地址：dialog 内 input
        try:
            page.locator('[data-test-id="DeclineButton"]').click(timeout=2000)
        except Exception:
            pass
        try:
            page.locator('input[data-test-id*="address" i], input[placeholder*="address" i], input[placeholder*="Enter" i]').first.fill('Mannerheimintie 1, Helsinki', timeout=4000)
            print('[addr] filled')
            page.wait_for_timeout(3000)
            dump(page, '05_address')
        except Exception as e:
            print('[addr] fail:', str(e)[:200])
            # 列出所有可见 input
            try:
                infos = page.evaluate("""() => {
                    const out = [];
                    document.querySelectorAll('input').forEach(i => {
                        const r = i.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0) out.push({ph: i.placeholder||'', tid: i.getAttribute('data-test-id')||'', type: i.type});
                    });
                    return out;
                }""")
                print('[inputs]', json.dumps(infos, ensure_ascii=False)[:1000])
            except Exception:
                pass
        page.wait_for_timeout(2000)
    except Exception as e:
        print('[fatal]', str(e)[:300])
    print('[total_reqs]', len(REQS))
    b.close()
print('DONE')
