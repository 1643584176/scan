# -*- coding: utf-8 -*-
"""B(viewer) 对 A 的公开 Weave 文件 AI 端点完整权限矩阵(重测)
对比上轮: threads 403→200 变化。测全部 AI 端点:
 - attachments / messages / make_versions / privacy_mode / make_all_private
 - 关键: B 能否读到消息内容(代码快照、对话)
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_THREAD = "28e728c0-dd4d-46e4-9b34-26cfb69e0aed"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


AC = load('ws_cookie_A_new.txt')
BC = load('ws_cookie_B_new.txt')


def call(label, method, path, uid, ck, body=None, query=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/make/" + A_MAKE, "Cookie": ck, "X-Figma-User-ID": uid}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:600]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:400]}")
        return e.code, raw
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:120]}")
        return None, str(e)


print("======== B(viewer) AI 端点矩阵 ========")
call("B attachments", "GET", f"/api/ai_chat/threads/{A_THREAD}/attachments", B_UID, BC)
call("B messages", "GET", f"/api/ai_chat/messages/{A_THREAD}", B_UID, BC,
     query={"owner_id": A_MAKE, "owner_type": "file"})
call("B make_versions", "GET", f"/api/ai_chat/{A_MAKE}/make_versions/{A_THREAD}", B_UID, BC)
call("B privacy_mode GET?", "GET", f"/api/ai_chat/{A_MAKE}/threads/{A_THREAD}/privacy_mode", B_UID, BC)
call("B make_all_private", "POST", f"/api/ai_chat/{A_MAKE}/threads/make_all_private", B_UID, BC, body={})
call("B privacy_mode POST", "POST", f"/api/ai_chat/{A_MAKE}/threads/{A_THREAD}/privacy_mode", B_UID, BC,
     body={"privacyMode": "private"})

print("\n======== A(owner) 基线 ========")
call("A attachments", "GET", f"/api/ai_chat/threads/{A_THREAD}/attachments", A_UID, AC)
call("A messages", "GET", f"/api/ai_chat/messages/{A_THREAD}", A_UID, AC,
     query={"owner_id": A_MAKE, "owner_type": "file"})
call("A make_versions", "GET", f"/api/ai_chat/{A_MAKE}/make_versions/{A_THREAD}", A_UID, AC)
