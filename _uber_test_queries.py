"""批量匿名调用 m.uber.com GraphQL 查询"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests
from playwright.sync_api import sync_playwright

# 拿 cookie
with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    page.goto('https://m.uber.com/go/home', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(5000)
    cookies = '; '.join(f'{c["name"]}={c["value"]}' for c in ctx.cookies())
    br.close()

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36',
    'Content-Type': 'application/json', 'Accept': '*/*',
    'Origin': 'https://m.uber.com', 'Referer': 'https://m.uber.com/go/home',
    'x-csrf-token': 'x',
    'x-uber-rv-initial-load-city-id': '2715',
    'x-uber-rv-session-type': 'desktop_session',
    'x-uber-client-name': 'web-plan',
    'Cookie': cookies,
}
URL = 'https://m.uber.com/go/graphql'
queries = json.load(open('_uber_queries.json', encoding='utf-8'))

tests = {
    'PudoCitySearch': {},
    'SavedPlaces': {},
    'PudoResolveLocation': {'id': 'san-francisco', 'latitude': 37.77, 'longitude': -122.41},
    'PudoLocationSearch': {'latitude': 37.77, 'longitude': -122.41, 'query': 'airport', 'type': 'PICKUP'},
}
for name, vars_ in tests.items():
    q = queries[name]['text']
    body = {'operationName': name, 'variables': vars_, 'query': q}
    r = requests.post(URL, headers=H, json=body, timeout=15)
    print(f'=== {name} -> {r.status_code} ===')
    print(f'    {r.text[:400]}')
    print()
