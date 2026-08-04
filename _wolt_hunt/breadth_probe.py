# -*- coding: utf-8 -*-
"""广度探测：对 flow_capture 中 Wolt 端点做匿名请求验证"""
import requests, json, sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

H = {
    'Origin': 'https://wolt.com',
    'App-Language': 'en', 'App-Locale': 'en',
    'X-HackerOne-Research': 'pccp',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0',
}

# flow_capture 中的 Wolt 端点 + 补充猜测
TESTS = [
    # restaurant-api
    ('GET', 'https://restaurant-api.wolt.com/v2/config'),
    ('GET', 'https://restaurant-api.wolt.com/v1/cities/58da504ba3284104e807127d/districts'),
    ('GET', 'https://restaurant-api.wolt.com/v1/consumer-api/address-fields?language=en'),
    ('GET', 'https://restaurant-api.wolt.com/v2/config/consents'),
    ('GET', 'https://restaurant-api.wolt.com/v1/pages/explore?lat=60.17&lon=24.94'),
    ('GET', 'https://restaurant-api.wolt.com/v1/pages/venue/slug/wolt-market-kamppi'),
    # consumer-api 其他
    ('POST', 'https://consumer-api.wolt.com/consumer-api/consents-router/v1/consent-enrollments-config', {"enrollments":[],"type":"tracking","platform":"web","is_bundle":True,"country":"fin"}),
    ('POST', 'https://consumer-api.wolt.com/regatta/consumer_client/exposures', {"variants":{"test":"treatment"}}),
    ('GET', 'https://consumer-api.wolt.com/consumer-api/v1/venues/60ebeb71c6904c2caf035f71'),
    ('GET', 'https://consumer-api.wolt.com/consumer-api/v1/venues/60ebeb71c6904c2caf035f71/menu'),
    # 搜索
    ('GET', 'https://restaurant-api.wolt.com/v1/pages/search?q=pizza&lat=60.17&lon=24.94'),
    ('GET', 'https://consumer-api.wolt.com/consumer-api/v1/search?q=pizza'),
    # 用户相关（匿名）
    ('GET', 'https://consumer-api.wolt.com/consumer-api/v1/users/me'),
    # dashapi
    ('POST', 'https://unified-gateway.dashapi.com/decision-systems/v1/dvedge/evaluation/evaluate-struct', {"names":["test"],"exposure_enabled":True}),
]

out = []
for method, url, *rest in TESTS:
    body = rest[0] if rest else None
    try:
        if method == 'GET':
            r = requests.get(url, headers=H, timeout=15)
        else:
            r = requests.post(url, json=body, headers=H, timeout=15)
        code = r.status_code
        txt = r.text[:350].replace('\n', ' ')
        ct = r.headers.get('Content-Type', '')[:50]
        out.append(f'{method} {url.split("/")[-2]}/{url.split("/")[-1].split("?")[0]}  -> {code} {ct[:30]} | {txt[:250]}')
    except Exception as e:
        out.append(f'{method} {url}  -> EXC {str(e)[:120]}')

open('D:/scan/_wolt_hunt/_breadth_probe.txt', 'w', encoding='utf-8').write('\n'.join(out))
print(f'DONE {len(out)} endpoints')
