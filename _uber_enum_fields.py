"""枚举 m.uber.com GraphQL 根字段（错误消息 oracle）"""
import sys, json, time, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    br = p.chromium.launch(channel='msedge', headless=False)
    ctx = br.new_context(viewport={'width': 1440, 'height': 900})
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

words = """
user users rider riders driver drivers trip trips meal meals restaurant restaurants
store stores order orders payment payments card cards wallet profile account
location locations address addresses fare price pricing estimate estimates
promo promos coupon coupons reward rewards rating ratings review reviews
receipt receipts invoice invoices message messages notification notifications
contact emergency settings preferences business fleet vehicle vehicles
document documents driverProfile support help faq feed home search history
saved favorite favorites token session auth login register verify email phone
verification code codes redemption redeem balance points point credit credits
gift giftCards giftCard loyalty membership subscription plan plans
pudoCitySearch pudoAutocomplete pudoSuggestions pudoLocationSearch pudoResolveLocation
wayfindingInstructions savedPlaces pudoFlights pudoResolveFlight pudoResolveInitialParams
pudoLocationRefinement currentUser currentUserProfile userProfile userInfo
appConfig config bootstrap experiments featureFlags flags remoteConfig
surgeMap availability vehiclesNearby eta priceEstimate fareEstimate
rideEstimate tripHistory pastTrips upcomingTrips receiptsList
driverDocuments driverEarnings driverRatings driverInfo
cities countries currencies languages translations locales
ads advertising sponsoredBrands
""".split()

print(f'测试 {len(words)} 个字段...')
found = []
for i, w in enumerate(words):
    body = {'operationName': 'Probe', 'query': f'query Probe {{ {w} }}'}
    try:
        r = requests.post(URL, headers=H, json=body, timeout=10)
        msg = ''
        try:
            msg = r.json()['errors'][0]['message']
        except Exception:
            pass
        if r.status_code == 200 or ('something went wrong' not in msg and msg):
            found.append((w, r.status_code, msg[:80]))
            print(f'  FOUND: {w} -> {r.status_code} {msg}')
    except Exception as e:
        print(f'  ERR: {w} {e}')
    time.sleep(0.25)

print()
print(f'=== 共发现 {len(found)} 个存在的字段 ===')
for w, s, m in found:
    print(f'  {w}: {s} {m}')
