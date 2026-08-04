# -*- coding: utf-8 -*-
"""黑盒枚举 order-xp 系列端点：区分 404(不存在)/401(需认证)/400-422(存在且匿名可达)/200"""
import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

H = {
    'Origin': 'https://wolt.com',
    'App-Language': 'en', 'App-Locale': 'en',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}
BASE = 'https://consumer-api.wolt.com'

PATHS = [
    # orders 创建/确认系列
    '/order-xp/web/v1/orders',
    '/order-xp/web/v2/orders',
    '/order-xp/web/v1/orders/place',
    '/order-xp/web/v2/orders/place',
    '/order-xp/web/v1/pages/order-confirmation',
    '/order-xp/web/v2/pages/order-confirmation',
    '/order-xp/web/v1/purchase',
    '/order-xp/web/v2/purchase',
    # carts/baskets 系列
    '/order-xp/web/v1/carts',
    '/order-xp/web/v2/carts',
    '/order-xp/web/v1/cart',
    '/order-xp/web/v2/cart',
    '/order-xp/web/v1/pages/cart',
    '/order-xp/web/v2/pages/cart',
    '/order-xp/web/v1/baskets',
    '/order-xp/web/v2/baskets',
    '/order-xp/web/v1/checkout',
    '/order-xp/web/v2/checkout',
    '/order-xp/web/v1/pages/checkout',
    # guest 系列
    '/order-xp/web/v1/orders/guest',
    '/order-xp/web/v2/orders/guest',
    '/order-xp/web/v1/guest/orders',
    '/order-xp/web/v2/guest/orders',
    # api 前缀
    '/order-xp/api/v1/orders',
    '/order-xp/api/v2/orders',
    '/order-xp/api/v1/carts',
    '/order-xp/api/v2/carts',
]

min_body = {"purchase_plan": {"venue": {"id": "60ebeb71c6904c2caf035f71", "country": "FIN", "currency": "EUR"}}}
lines = []
for p in PATHS:
    try:
        r = requests.post(BASE + p, json=min_body, headers=H, timeout=15)
        code, body = r.status_code, r.text[:220].replace('\n', ' ')
    except Exception as e:
        lines.append(f'{p} -> EXC {e}')
        continue
    lines.append(f'{p} -> {code} :: {body}')
    # 顺便 GET 探测
    try:
        r2 = requests.get(BASE + p, headers=H, timeout=15)
        lines.append(f'GET {p} -> {r2.status_code}')
    except Exception:
        pass

open('_wolt_hunt/_order_enum.txt', 'w', encoding='utf-8').write('\n'.join(lines))
print('DONE', len(lines))
