"""批量匿名测试 www.uber.com RPC 端点（从 JS 提取的操作名）"""
import sys, json, time, requests
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

ops = [
    'getUserPersonalizedData', 'getUberCashBalance', 'getUserRating', 'getUserTravelStatus',
    'getMembershipAttributes', 'getUpcomingActivities', 'getAdminToolAccess', 'getBugReportingAccess',
    'getXpTreatmentsAccess', 'getXpData', 'getPesData', 'getCarRentalProductSelectionPreview',
    'getCarRentalProductSelectionV2', 'getCitySearch', 'loadPlaceDetails', 'loadPlaceDetailsByCoordinates',
    'loadCurrentLocation', 'loadSuggestions', 'loadDriverGuarantee', 'loadReferralGuarantee',
    'getPromoPill', 'hasActiveCow', 'getSupportedLocales', 'getTrainDepartureOptions',
    'getMapHeroEnabledProducts', 'getBlockExperiments', 'getExperiments', 'isWebview',
    'getProductSuggestions', 'getMerchandisingAdAvailability', 'getCurrentUser',
]
bodies = {
    'getCitySearch': {'query': 'san francisco'},
    'loadPlaceDetails': {'placeId': 'ChIJIQBpAG2ahYAR_6128GcTUEo'},
    'loadPlaceDetailsByCoordinates': {'latitude': 37.77, 'longitude': -122.41},
    'loadSuggestions': {'latitude': 37.77, 'longitude': -122.41},
    'loadCurrentLocation': {'latitude': 37.77, 'longitude': -122.41},
    'getTrainDepartureOptions': {'stationId': '1'},
    'getCarRentalProductSelectionPreview': {'latitude': 37.77, 'longitude': -122.41},
}

found = []
for i, op in enumerate(ops):
    body = bodies.get(op, {})
    url = f'https://www.uber.com/api/{op}?localeCode=en-US'
    try:
        r = requests.post(url, headers=H, json=body, timeout=12)
        txt = r.text[:400]
        status = 'OK' if r.status_code == 200 else f'HTTP{r.status_code}'
        found.append((op, r.status_code, txt))
        print(f'[{status}] {op}')
        print(f'    {txt}')
        print()
    except Exception as e:
        print(f'[ERR] {op}: {e}')
    time.sleep(0.4)

print(f'\n=== {len(found)} 个端点测试完成 ===')
