# -*- coding: utf-8 -*-
"""waw-api/corporate portal 无认证基线探测（只读 GET，低频，带 research 头）
目标：确认哪些企业端接口无认证可触达（L0/L1 证据）
"""
import requests, json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://corporate.wolt.com",
    "X-HackerOne-Research": "pccp",
    "Accept": "application/json",
}

def probe(m, url, body=None, params=None):
    try:
        r = requests.request(m, url, headers=H, json=body, params=params, timeout=15)
        txt = r.text.replace("\n", " ")[:220]
        return f"{r.status_code} | {txt}"
    except Exception as e:
        return f"ERR {e}"

R = "https://restaurant-api.wolt.com"      # scope 内
C = "https://corporate-service.wolt.com"   # corporate.wolt.com 功能后端

tests = [
    ("GET",  R + "/v1/waw-api/user-permissions", None, None, "企业角色权限(无认证)"),
    ("GET",  R + "/v1/waw-api/corporates", None, {"name": "wolt", "pagination": "false"}, "企业搜索(无认证)"),
    ("GET",  R + "/v1/waw-api/agreement-parties", None, None, "协议方列表(无认证)"),
    ("GET",  R + "/v1/waw-api/country-configs", None, None, "国家配置(无认证)"),
    ("POST", R + "/v1/opstools/users/search", {"q": "a"}, None, "Wolt用户搜索(无认证)"),
    ("GET",  C + "/v1/corporates", None, None, "corporate-service 企业列表(无认证)"),
    ("GET",  C + "/portal-api/v1/corporates", None, None, "portal-api 企业列表(无认证)"),
    ("GET",  C + "/v1/alerts", None, None, "alerts(无认证)"),
]

print(f"{'#':<3}{'方法':<5}{'URL':<70}{'结果'}")
for i, (m, url, body, params, note) in enumerate(tests):
    res = probe(m, url, body, params)
    print(f"{i:<3}{m:<5}{url:<70}{res}")
    print(f"    -- {note}")
print("\nDONE")
