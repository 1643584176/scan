"""用浏览器 cookie 复现 m.uber.com/go/graphql 调用 + introspection"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900},
                         user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
    page = ctx.new_page()
    page.goto('https://m.uber.com/go/home', timeout=60000, wait_until='domcontentloaded')
    page.wait_for_timeout(6000)
    cookies = '; '.join(f'{c["name"]}={c["value"]}' for c in ctx.cookies())
    br.close()

H = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Origin': 'https://m.uber.com',
    'Referer': 'https://m.uber.com/go/home',
    'x-csrf-token': 'x',
    'x-uber-rv-initial-load-city-id': '2715',
    'x-uber-rv-session-type': 'desktop_session',
    'x-uber-client-name': 'web-plan',
    'Cookie': cookies,
}
URL = 'https://m.uber.com/go/graphql'

r = requests.post(URL, headers=H, json={'query': '{__typename}'}, timeout=15)
print(f'{__name__} {__file__}')
print(f'{{__typename}} -> {r.status_code}: {r.text[:200]}')

r2 = requests.post(URL, headers=H, json={'query': '{__schema{queryType{name} mutationType{name}}}'}, timeout=15)
print(f'introspection -> {r2.status_code}: {r2.text[:400]}')

# 完整 introspection（如果上面成功）
if r2.status_code == 200 and '"data"' in r2.text:
    full = requests.post(URL, headers=H, json={'query': '''query { __schema { queryType { name } mutationType { name } types { name kind } } }'''}, timeout=20)
    open('_uber_schema_types.json', 'w', encoding='utf-8').write(full.text)
    print(f'完整 schema types 已保存 ({len(full.text)} bytes)')
