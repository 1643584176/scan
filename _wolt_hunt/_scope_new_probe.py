# -*- coding: utf-8 -*-
"""scope 内未测接口最小探测（全部路径来自 JS dump，host 来自真实流量，带 research 头）
只读/最小 POST，低频，仅确认存活与行为，为深入验证定位
"""
import requests, json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://wolt.com",
    "X-HackerOne-Research": "pccp",
    "Content-Type": "application/json",
    "App-Language": "en",
}

def probe(m, url, body=None, params=None):
    try:
        r = requests.request(m, url, headers=HDR, json=body, params=params, timeout=12)
        txt = r.text.replace("\n", " ")[:160]
        return f"{r.status_code} | {txt}"
    except Exception as e:
        return f"ERR {e}"

C = "https://consumer-api.wolt.com"
R = "https://restaurant-api.wolt.com"
W = "https://wolt.com"

tests = [
    # (method, url, body, params, 说明)
    ("GET",  R + "/v2/config/consents", None, None, "基线(已知200)"),
    ("GET",  C + "/order-xp/v1/baskets/count", None, None, "购物车计数-无认证"),
    ("GET",  C + "/order-xp/web/v1/pages/orders", None, None, "订单列表-无认证"),
    ("GET",  C + "/order-xp/v1/restricted-items/user-consents", None, None, "受限商品同意"),
    ("GET",  C + "/v2/notifications", None, None, "通知-无认证"),
    ("GET",  W + "/v1/waw-api/signup-countries", None, None, "企业注册国家(公开?)"),
    ("GET",  W + "/v1/waw-api/user-permissions", None, None, "企业用户权限(公开?)"),
    ("POST", W + "/v1/converse-guest-token", {"hcaptchaToken": ""}, None, "客服guest-token-空token"),
    ("POST", C + "/v1/group_order/", {}, None, "团购创建-空体"),
    ("GET",  C + "/order-xp/v1/baskets/count", None, {"q": "1"}, "带参变体"),
    ("POST", W + "/v1/log", {"type": "Test", "payload": {}}, None, "log端点(已知200基线)"),
]

print(f"{'#':<3}{'方法':<5}{'URL':<75}{'结果'}")
for i, (m, url, body, params, note) in enumerate(tests):
    res = probe(m, url, body, params)
    print(f"{i:<3}{m:<5}{url:<75}{res}")
    print(f"    -- {note}")
print("\nDONE")
