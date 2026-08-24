# -*- coding: utf-8 -*-
# code_connect 未测端点参数契约迭代: 空body -> 400 typechecking 错误泄露参数名/类型
# 目标: 拿到 bulk_map / user_rules / code_snippet / generate_template / libraries/repositories 的入参契约
import io, json, sys
import requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

FK = "bv2nMIdFf4u3dESGail4sm"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
CKB = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
HDR = {"Origin": "https://www.figma.com", "Referer": f"https://www.figma.com/file/{FK}",
       "User-Agent": UA, "Content-Type": "application/json", "Cookie": CKB}

EPS = [
    ("POST", "/api/code_connect/bulk_map"),
    ("DEL",  "/api/code_connect/bulk_map"),
    ("PUT",  "/api/code_connect/user_rules"),
    ("POST", "/api/code_connect/code_snippet"),
    ("POST", "/api/code_connect/generate_template"),
    ("POST", "/api/code_connect/libraries/repositories"),
]

def probe(method, path, body):
    r = requests.request(method, f"https://www.figma.com{path}",
                         headers=HDR, json=body, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, r.text[:300]

for m, p in EPS:
    st, j = probe(m, p, {})
    print(f"\n== {m} {p} (empty body) -> {st}")
    s = json.dumps(j, ensure_ascii=False)
    print(s[:600])
