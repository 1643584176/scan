import requests, json

h = {'User-Agent': 'Mozilla/5.0', 'Origin': 'https://wolt.com'}

targets = [
    'https://authentication.wolt.com/',
    'https://authentication.wolt.com/v1/',
    'https://authentication.wolt.com/health',
    'https://converse-api.wolt.com/',
    'https://converse-api.wolt.com/v1/',
    'https://converse-api.development.dev.woltapi.com/',
    'https://converse-api.development.dev.woltapi.com/v1/',
    'https://converse-api.development.dev.woltapi.com/conveyer/',
]

for url in targets:
    try:
        r = requests.get(url, headers=h, timeout=10, allow_redirects=False)
        ct = r.headers.get('content-type', '')[:40]
        print(f'{url}')
        print(f'  -> {r.status_code} | {ct} | {r.text[:120].strip()[:120]}')
    except Exception as e:
        print(f'{url}')
        print(f'  -> ERR: {str(e)[:80]}')
    print()
