"""匿名获取私有文件 - 路径变换测试
目标：匿名(无cookie)通过不同路径获取私有文件数据
被拒基准：file_metadata 403、OpenEditorFileData 返回空
变换路径：
  A. HTTP /api/versions/{key}（版本历史接口，权限可能不同）
  B. WS URL preload 参数带 OpenEditorFileData(私有key)（preload 路径 vs subscribe 消息路径）
  C. WS subscribe FileCanUseDevModeDemoFile(key=私有key)（同资源不同视图）
  D. WS auth clientType=desktop + subscribe OpenEditorFileData（客户端类型变换）
"""
import json, sys, time, urllib.parse
import requests
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PRIVATE_FILE = "qzDqStIDJyGbthpKiuvfwg"  # 匿名 HTTP 403 确认私有
PUBLIC_FILE = "bv2nMIdFf4u3dESGail4sm"
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
HASH_OPEN_EDITOR = "3d578d4859a5845c2f037014898cd2e84f17ac3961ec9fa4b7f1d06c302e63c1"
HASH_DEV_MODE = "71f2e28d59b7dd5cb843ca69e89d4b8ee17de0a0acfe265c7c3fb2d0e91d38de"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"

WS_URL_ANON = open(r"D:\scan\_figma_hunt\ws_url_anon.txt").read().strip()


def test_a_http_versions():
    print("\n[A] HTTP /api/versions/{key} 匿名")
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json",
                      "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/"})
    for k, label in ((PRIVATE_FILE, "私有"), (PUBLIC_FILE, "公开")):
        r = s.get(f"https://www.figma.com/api/versions/{k}?page_size=200", timeout=15)
        print(f"  [{label}] {r.status_code} len={len(r.text)} {r.text[:120]!r}")


def ws_connect(url):
    return websocket.create_connection(url, timeout=20, origin="https://www.figma.com",
                                       header=[f"User-Agent: {UA}"])


def recv_until(ws, wait, view_name, filter_key):
    hits = []
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(3, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode != 0x1:
                continue
            try:
                msg = json.loads(data)
            except Exception:
                continue
            mt = msg.get("messageType", "?")
            if mt == "denormalizedPendingMutations":
                for key, payload in msg.get("mutations", {}).items():
                    if filter_key in key:
                        hits.append((key, payload))
            elif mt == "error":
                hits.append(("ERROR", msg))
        except Exception:
            break
    return hits


def test_b_preload():
    print("\n[B] 匿名 WS + URL preload 带 OpenEditorFileData(私有文件)")
    q = urllib.parse.urlparse(WS_URL_ANON).query
    params = urllib.parse.parse_qs(q)
    preload = {"OpenEditorFileData": {"hash": HASH_OPEN_EDITOR, "args": {"fileKey": PRIVATE_FILE}}}
    params["preload"] = [json.dumps(preload, separators=(",", ":"))]
    url = f"wss://www.figma.com/api/livegraph?{urllib.parse.urlencode({k: v[0] for k, v in params.items()})}"
    ws = ws_connect(url)
    auth = {"messageType": "auth", "clientType": "web",
            "args": {"userId": None, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": COMMIT,
                     "clientUrl": "https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm"},
            "clientRequestedVersion": 2}
    ws.send(json.dumps(auth))
    hits = recv_until(ws, 8, "OpenEditorFileData", "OpenEditorFileData")
    ws.close()
    for k, p in hits:
        s = json.dumps(p, ensure_ascii=False) if isinstance(p, dict) else str(p)
        print(f"  [{'ERR' if k=='ERROR' else 'HIT'}] {s[:300]}")
    print(f"  共 {len(hits)} 条")


def test_c_other_view():
    print("\n[C] 匿名 subscribe FileCanUseDevModeDemoFile(私有文件)")
    ws = ws_connect(WS_URL_ANON)
    ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                        "args": {"userId": None, "anonymousUserId": None},
                        "tags": {"clientType": "web", "commitHash": COMMIT,
                                 "clientUrl": "https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm"},
                        "clientRequestedVersion": 2}))
    time.sleep(2)
    ws.send(json.dumps({"messageType": "subscribe", "viewName": "FileCanUseDevModeDemoFile",
                        "viewHash": HASH_DEV_MODE, "loadType": "initial",
                        "args": {"key": PRIVATE_FILE}}))
    hits = recv_until(ws, 8, "FileCanUseDevModeDemoFile", "FileCanUseDevModeDemoFile")
    ws.close()
    for k, p in hits:
        s = json.dumps(p, ensure_ascii=False) if isinstance(p, dict) else str(p)
        print(f"  [{'ERR' if k=='ERROR' else 'HIT'}] {s[:300]}")
    print(f"  共 {len(hits)} 条")


def test_d_client_type():
    print("\n[D] 匿名 WS clientType=desktop + subscribe OpenEditorFileData(私有文件)")
    ws = ws_connect(WS_URL_ANON)
    ws.send(json.dumps({"messageType": "auth", "clientType": "desktop",
                        "args": {"userId": None, "anonymousUserId": None},
                        "tags": {"clientType": "desktop", "commitHash": COMMIT,
                                 "clientUrl": "https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm"},
                        "clientRequestedVersion": 2}))
    time.sleep(2)
    ws.send(json.dumps({"messageType": "subscribe", "viewName": "OpenEditorFileData",
                        "viewHash": HASH_OPEN_EDITOR, "loadType": "initial",
                        "args": {"fileKey": PRIVATE_FILE}}))
    hits = recv_until(ws, 8, "OpenEditorFileData", "OpenEditorFileData")
    ws.close()
    for k, p in hits:
        s = json.dumps(p, ensure_ascii=False) if isinstance(p, dict) else str(p)
        print(f"  [{'ERR' if k=='ERROR' else 'HIT'}] {s[:300]}")
    print(f"  共 {len(hits)} 条")


if __name__ == "__main__":
    test_a_http_versions()
    test_b_preload()
    test_c_other_view()
    test_d_client_type()
    print("\n===== 完成 =====")
