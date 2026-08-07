"""批量匿名复现 www.uber.com /api/* 端点"""
import sys, json, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

cookies = json.load(open('_uber_www_cookies.json', encoding='utf-8'))
cookie_str = '; '.join(f'{c["name"]}={c["value"]}' for c in cookies)

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36',
    'Content-Type': 'application/json', 'Accept': '*/*',
    'Origin': 'https://www.uber.com', 'Referer': 'https://www.uber.com/',
    'x-csrf-token': 'x',
    'Cookie': cookie_str,
}

tests = [
    ('getCurrentUser', '{}'),
    ('getMapHeroEnabledProducts', '{}'),
    ('getProductSuggestions', '{"type":"DEFAULT"}'),
    ('getProductSuggestions', '{"type":"CUSTOM","useExpandedData":false}'),
    ('getMerchandisingAdAvailability', '{"redirectUrl":"https://m.uber.com/reserve"}'),
    ('isWebview', '{}'),
    ('getBlockExperiments', '{}'),
    ('getExperiments', '{}'),
    ('pudoLocationSearch', '{"latitude":37.3265,"longitude":126.2526,"query":"airport","type":"PICKUP"}'),
]
for name, body in tests:
    url = f'https://www.uber.com/api/{name}?localeCode=en-US'
    r = requests.post(url, headers=H, data=body, timeout=15)
    print(f'=== {name} ({body[:60]}) -> {r.status_code} ===')
    print(f'    {r.text[:600]}')
    print()
