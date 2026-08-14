# -*- coding: utf-8 -*-
"""批量测试匿名 JSON 托管服务:创建 -> 检查响应头(ct/cc) -> MCP probe 错误分类
目标:找到 content-type=application/json + cache-control=public 的载体
"""
import json, time, uuid as uuid_mod
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
MCP = "https://catalog.shopify.com/api/ucp/mcp"
PAYLOAD = json.dumps({"ucp": {"version": "2026-04-08"}})

def mcp_probe(label, profile_url):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": "search_catalog", "arguments": {"meta": {"ucp-agent": {"profile": profile_url}}, "query": "shoes"}}}
    t0 = time.time()
    try:
        r = requests.post(MCP, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
        print(f"[MCP {label}] {time.time()-t0:.1f}s | {r.text[:180]}", flush=True)
    except Exception as e:
        print(f"[MCP {label}] ERROR {type(e).__name__}", flush=True)

def check(label, url):
    try:
        r = requests.get(url, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
        print(f"[GET {label}] HTTP {r.status_code} ct={r.headers.get('Content-Type')} cc={r.headers.get('Cache-Control')} | {r.text[:80]}", flush=True)
        return r.status_code == 200
    except Exception as e:
        print(f"[GET {label}] ERROR {type(e).__name__}", flush=True)
        return False

def try_service(name, create_fn):
    print(f"\n===== {name} =====", flush=True)
    try:
        url = create_fn()
        if not url:
            print(f"[{name}] create failed", flush=True)
            return
        ok = check(name, url)
        if ok:
            time.sleep(0.5)
            mcp_probe(name, url)
    except Exception as e:
        print(f"[{name}] EXC {type(e).__name__} {e}", flush=True)

if __name__ == "__main__":
    # 1. jsonblob(重试)
    try_service("jsonblob", lambda: requests.post("https://jsonblob.com/api/jsonBlob", json=json.loads(PAYLOAD), headers=H, proxies=PROXY, impersonate="chrome", timeout=25).headers.get("Location"))
    # 2. npoint
    try_service("npoint", lambda: requests.post("https://api.npoint.io/", json=json.loads(PAYLOAD), headers=H, proxies=PROXY, impersonate="chrome", timeout=25).json().get("href"))
    # 3. 0x0.st
    def f_0x0():
        r = requests.post("https://0x0.st", files={"file": ("p.json", PAYLOAD, "application/json")}, headers={"User-Agent": H["User-Agent"]}, proxies=PROXY, impersonate="chrome", timeout=30)
        return r.text.strip()
    try_service("0x0.st", f_0x0)
    # 4. paste.rs
    def f_pasters():
        r = requests.post("https://paste.rs", data=PAYLOAD, headers={"User-Agent": H["User-Agent"], "Content-Type": "application/json"}, proxies=PROXY, impersonate="chrome", timeout=30)
        return r.text.strip()
    try_service("paste.rs", f_pasters)
    # 5. dpaste
    def f_dpaste():
        r = requests.post("https://dpaste.org/api/", data={"content": PAYLOAD, "syntax": "json", "expiry_days": "30"}, headers={"User-Agent": H["User-Agent"]}, proxies=PROXY, impersonate="chrome", timeout=30)
        return r.headers.get("Location")
    try_service("dpaste", f_dpaste)
    # 6. rentry
    def f_rentry():
        r = requests.post("https://rentry.co/api/new", data={"content": PAYLOAD}, headers={"User-Agent": H["User-Agent"]}, proxies=PROXY, impersonate="chrome", timeout=30)
        j = r.json()
        return "https://rentry.co/" + j.get("url") + "/raw" if j.get("url") else None
    try_service("rentry", f_rentry)
    # 7. keyvalue.xyz(重试)
    def f_kv():
        r = requests.post("https://keyvalue.xyz/new/json", data=PAYLOAD, headers={"User-Agent": H["User-Agent"], "Content-Type": "application/json"}, proxies=PROXY, impersonate="chrome", timeout=30)
        return r.text.strip()
    try_service("keyvalue", f_kv)
    # 8. jsonkeeper(正确 API)
    def f_jk():
        r = requests.post("https://www.jsonkeeper.com/api/upload", data=PAYLOAD, headers={"User-Agent": H["User-Agent"], "Content-Type": "application/json"}, proxies=PROXY, impersonate="chrome", timeout=30)
        print(f"  [jk resp] {r.text[:100]}", flush=True)
        return r.text.strip()
    try_service("jsonkeeper", f_jk)
    # 9. mocky(重试)
    def f_mocky():
        r = requests.post("https://api.mocky.io/api/mock", json={"status": 200, "content": PAYLOAD, "content_type": "application/json"}, headers=H, proxies=PROXY, impersonate="chrome", timeout=30)
        print(f"  [mocky resp] {r.text[:150]}", flush=True)
        return r.json().get("link") if r.status_code == 200 else None
    try_service("mocky", f_mocky)
    # 10. 对照:httpbin response-headers(头可控,body 固定)
    try_service("httpbin-hdr", lambda: "https://httpbin.org/response-headers?Cache-Control=public%2C%20max-age%3D3600&Content-Type=application%2Fjson")
    # 11. httpbingo(镜像)
    try_service("httpbingo-hdr", lambda: "https://httpbingo.org/response-headers?Cache-Control=public%2C%20max-age%3D3600&Content-Type=application%2Fjson")
    # 12. postman-echo response-headers
    try_service("postman-hdr", lambda: "https://postman-echo.com/response-headers?Cache-Control=public%2C%20max-age%3D3600")
