# -*- coding: utf-8 -*-
"""X-Figma-User-ID 头精确测绘: 真实uid vs 随机uid vs 另一真实uid 在各接口的效果
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
A_THREAD = "ee5997d9-bbdb-4912-9587-9022c14c0be0"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, path, query=None, xuid=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    if xuid is not None:
        headers["X-Figma-User-ID"] = xuid
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:100]}")
            return r.status
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:100]}")
        return e.code


CASES = [
    ("无X-UID", None),
    ("X-UID=A(真实owner)", A_UID),
    ("X-UID=B(另一真实用户)", B_UID),
    ("X-UID=随机", "99999999999999999999"),
]
for label, xuid in CASES:
    print(f"\n--- {label} ---")
    call("file_metadata", "/api/file_metadata/" + A_DESIGN, xuid=xuid)
    call("threads", "/api/ai_chat/threads",
         {"owner_id": A_DESIGN, "owner_type": "file"}, xuid=xuid)
    call("messages", f"/api/ai_chat/messages/{A_THREAD}",
         {"owner_id": A_DESIGN, "owner_type": "file"}, xuid=xuid)
    call("make_versions", f"/api/ai_chat/{A_DESIGN}/make_versions/{A_THREAD}", xuid=xuid)
