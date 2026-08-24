# -*- coding: utf-8 -*-
"""AI Chat 线程资源级细节探测:B 用 A 的 threadId 读附件/消息/版本
目标结果: B 读取到 A 线程的附件元数据/消息内容/Make 版本列表
"""
import io, json, sys, urllib.error, urllib.request
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
        import urllib.parse as up
        url += "?" + up.urlencode(query)
    req = urllib.request.Request(url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:700]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:700]}")
        return e.code, raw


print("======== 1. 线程附件列表 ========")
call("A read own thread attachments", "GET", f"/api/ai_chat/threads/{A_THREAD}/attachments", A_UID, AC)
call("B read A thread attachments ⭐", "GET", f"/api/ai_chat/threads/{A_THREAD}/attachments", B_UID, BC)

print()
print("======== 2. Make 版本列表 ========")
call("A read own make versions", "GET", f"/api/ai_chat/{A_MAKE}/make_versions/{A_THREAD}", A_UID, AC)
call("B read A make versions ⭐", "GET", f"/api/ai_chat/{A_MAKE}/make_versions/{A_THREAD}", B_UID, BC)

print()
print("======== 3. 线程消息列表 ========")
call("A read own thread messages", "GET", f"/api/ai_chat/messages/{A_THREAD}", A_UID, AC,
     query={"owner_id": A_MAKE, "owner_type": "file"})
call("B read A thread messages ⭐", "GET", f"/api/ai_chat/messages/{A_THREAD}", B_UID, BC,
     query={"owner_id": A_MAKE, "owner_type": "file"})
