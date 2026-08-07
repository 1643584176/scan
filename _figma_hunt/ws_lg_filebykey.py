"""livegraph FileByKey view 匿名 vs 登录 测试

view 定义（JS 确定性来源）：
  FileByKey: args=[{name:"fileKey"}], fields={file: fileV2{key, libraryKey, canEdit, canRead, ...}}

创造目标：匿名 subscribe FileByKey + 任意 fileKey →
  1. 返回 canRead/canEdit = 权限探测（私有文件存在性+权限）
  2. 若返回 fileV2 更多字段（name/thumbnail）= 文件元数据泄露
"""
import json, sys, time, base64, uuid
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
COOKIE = "; ".join(f"{c['name']}={c['value']}" for c in SESS if c.get("name") and c.get("value"))

PRIVATE = "qzDqStIDJyGbthpKiuvfwg"
PUBLIC = "bv2nMIdFf4u3dESGail4sm"
GHOST_KEY = "zzzzzzzzzzzzzzzzzzzzzz"

HASH = "f25ed3eceb859f73d4484895786b72fcf082f473c83967f96136f7fa8d0f05b4"


def url_for(team_id="1666382706663462213"):
    pre = base64.b64encode(json.dumps({"CurrentTeamCombinedPermissions": {"hash": HASH, "args": {"teamId": team_id}}}).encode()).decode()
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=e5b828076698c1d9&pt=1786081987&ph=9xNUKy_inuuDiWuwhw6JnjwpvMtdcdgfBBpeeeunrp0"
            f"&userId=1666382703778278399&anonUserId=09725c80-4313-4749-9eda-a73821e1496e&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload={pre}&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Fdesign%2FqzDqStIDJyGbthpKiuvfwg%2Ftest&connectionType=initial&reconnect=0")


def sub(name, file_key, use_cookie, view="FileByKey", wait=5):
    headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"]
    if use_cookie:
        headers.append(f"Cookie: {COOKIE}")
    try:
        ws = websocket.create_connection(url_for(), timeout=15, origin="https://www.figma.com", header=headers)
    except Exception as e:
        print(f"  {name}: 握手失败 {type(e).__name__}")
        return
    msg = {"messageType": "subscribe", "viewName": view, "viewHash": HASH,
           "loadType": "Initial", "args": {"fileKey": file_key}, "traceId": str(uuid.uuid4())}
    try:
        ws.send(json.dumps(msg))
    except Exception as e:
        print(f"  {name}: send 失败 {e}")
        ws.close()
        return
    got = []
    closed = False
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(2, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode == 0x8:
                closed = True
                break
            if opcode in (1, 2):
                got.append(data)
        except websocket.WebSocketTimeoutException:
            continue
        except Exception:
            closed = True
            break
    ws.close()
    print(f"  {name}: {'CLOSE' if closed else '保持'}, 收到 {len(got)} 条")
    for g in got[:6]:
        s = g.decode(errors="replace")
        if "denormalized" in s or "error" in s.lower() or "sync" in s.lower():
            print(f"     {s[:400]}")


if __name__ == "__main__":
    print("=== FileByKey 匿名 vs 登录 ===")
    sub("匿名+私有文件", PRIVATE, False)
    sub("登录+私有文件", PRIVATE, True)
    sub("匿名+公开文件", PUBLIC, False)
    sub("匿名+ghost key", GHOST_KEY, False)
