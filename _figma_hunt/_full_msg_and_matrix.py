# -*- coding: utf-8 -*-
"""完整抓取 A 私有 design 的 AI 对话(含 assistant 回复) + 注入矩阵
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
A_THREAD_DESIGN = "ee5997d9-bbdb-4912-9587-9022c14c0be0"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


BC = load('ws_cookie_B_new.txt')


def call(label, path, query=None, uid_hdr=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    if uid_hdr:
        headers["X-Figma-User-ID"] = uid_hdr
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            return r.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')


print("======== A 私有 design 完整 AI 对话(B 冒充 A) ========")
st, raw = call("messages full", f"/api/ai_chat/messages/{A_THREAD_DESIGN}",
               query={"owner_id": A_DESIGN, "owner_type": "file", "fuid": A_UID})
print("HTTP", st, "len", len(raw))
try:
    j = json.loads(raw)
    msgs = j.get("meta", {}).get("messages", [])
    print(f"消息数: {len(msgs)}")
    for m in msgs:
        print(f"\n--- msg {m.get('id')} role={m.get('role')} index={m.get('index')} created={m.get('created_at')}")
        for p in m.get("parts", []):
            ct = p.get("content_json", "")
            try:
                cj = json.loads(ct)
                if "text" in cj:
                    print(f"  [{p.get('part_type')}] text: {cj['text'][:500]}")
                else:
                    print(f"  [{p.get('part_type')}] {ct[:300]}")
            except Exception:
                print(f"  [{p.get('part_type')}] {ct[:300]}")
except Exception as e:
    print("parse err:", e, raw[:500])

print("\n======== 注入矩阵: fuid query vs X-UID header ========")
tests = [
    ("file_metadata fuid", f"/api/file_metadata/{A_DESIGN}", {"fuid": A_UID}, None),
    ("file_metadata X-UID", f"/api/file_metadata/{A_DESIGN}", None, A_UID),
    ("realtime_token fuid", f"/api/files/{A_DESIGN}/realtime_token", {"fuid": A_UID}, None),
    ("realtime_token X-UID", f"/api/files/{A_DESIGN}/realtime_token", None, A_UID),
    ("threads fuid", "/api/ai_chat/threads", {"owner_id": A_DESIGN, "owner_type": "file", "fuid": A_UID}, None),
    ("threads X-UID", "/api/ai_chat/threads", {"owner_id": A_DESIGN, "owner_type": "file"}, A_UID),
    ("messages fuid", f"/api/ai_chat/messages/{A_THREAD_DESIGN}",
     {"owner_id": A_DESIGN, "owner_type": "file", "fuid": A_UID}, None),
    ("messages X-UID", f"/api/ai_chat/messages/{A_THREAD_DESIGN}",
     {"owner_id": A_DESIGN, "owner_type": "file"}, A_UID),
]
for label, path, query, uid_hdr in tests:
    st, raw = call(label, path, query=query, uid_hdr=uid_hdr)
    ok = "✅" if st == 200 else "❌"
    print(f"{ok} [{label}] HTTP {st}")
