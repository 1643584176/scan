"""批量匿名测试全部扩展后的查询"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import requests
from playwright.sync_api import sync_playwright

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
queries = json.load(open('_uber_queries_full2.json', encoding='utf-8'))

vars_map = {
    'PudoResolveInitialParams': {'includePickup': True, 'includeDrop0': False, 'includeDrop1': False, 'includeDrop2': False, 'includeDrop3': False, 'includeDrop4': False, 'includeFlight': False, 'flightID': 'F-00000000000000', 'pickupID': 'ChIJIQBpAG2ahYAR_6128GcTUEo'},
    'PudoResolveLocation': {'id': 'ChIJIQBpAG2ahYAR_6128GcTUEo', 'latitude': 37.77, 'longitude': -122.41},
    'PudoLocationSearch': {'latitude': 37.77, 'longitude': -122.41, 'query': 'airport', 'type': 'PICKUP'},
    'PudoAutocompleteBase': {'query': 'san francisco'},
    'PudoSuggestions': {'includeDestinations': True, 'includeOrigins': True, 'includeAirportTerminals': True, 'includeRAPUStatus': True, 'latitude': 37.77, 'longitude': -122.41},
    'PudoFlights': {'query': 'SFO', 'departureTimeMsec': 1786000000000.0, 'pageSize': 5},
    'PudoResolveFlight': {'id': 'F-00000000000000'},
    'WayfindingInstructions': {'accessPointId': 'ChIJIQBpAG2ahYAR_6128GcTUEo'},
    'PudoLocationRefinement': {'pickup': {'latitude': 37.77, 'longitude': -122.41}, 'vvid': 0, 'query': 'airport', 'type': 'PICKUP'},
    'PudoResolveLocationPudoFragment': {'id': 'ChIJIQBpAG2ahYAR_6128GcTUEo'},
}
for name, info in queries.items():
    q = info['text']
    v = vars_map.get(name, {})
    body = {'operationName': name, 'variables': v, 'query': q}
    r = requests.post(URL, headers=H, json=body, timeout=15)
    err = ''
    try:
        j = r.json()
        if 'errors' in j:
            err = str(j['errors'][0].get('message', ''))[:100]
        data = json.dumps(j.get('data', {}))[:220]
    except Exception:
        data = r.text[:220]
    status = 'ERR' if err else 'OK'
    print(f'[{status}] {name} {r.status_code} err={err}')
    print(f'    {data}')
    print()
