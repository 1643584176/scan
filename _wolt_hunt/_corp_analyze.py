# -*- coding: utf-8 -*-
"""corporate_main.js 分析：提取 waw-api / corporate-service 全部调用与上下文"""
import re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

data = open(r"D:\scan\_wolt_hunt\corporate_main.js", encoding="utf-8", errors="replace").read()

print("=== waw-api 路径 ===")
seen = set()
for m in re.finditer(r"/v1/waw-api[^\"'\x60\s,)]*", data):
    u = m.group(0)
    if u not in seen:
        seen.add(u)
        print(u)

print("\n=== corporate-service 路径(Fp/含 b2b-config/webhooks/delivery-orders) ===")
seen2 = set()
for m in re.finditer(r'["\'`](/v1/(?:corporate|corporates|delivery-orders|webhooks|admin|utils|opstools|alerts|merchants|middleware-partners)[^"\'`]*)?["\'`]', data):
    u = m.group(1)
    if u and u not in seen2:
        seen2.add(u)
        print(u)

print("\n=== 各路径归属客户端(上下文 300 字符) ===")
for kw in ["/v1/waw-api/user-permissions", "/v1/waw-api/corporates", "/v1/corporates", "/v1/webhooks", "/v1/delivery-orders", "/v1/admin/seven-eleven", "/v1/utils/send-email", "/v1/opstools/users/search"]:
    ms = list(re.finditer(re.escape(kw), data))
    print(f"\n-- {kw} ({len(ms)} 处)")
    for m in ms[:2]:
        s = max(0, m.start() - 260)
        e = min(len(data), m.end() + 100)
        print("   ", re.sub(r"\s+", " ", data[s:e])[:360])
