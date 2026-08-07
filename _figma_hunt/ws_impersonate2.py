"""Figma livegraph WS 身份叠加创造测试（第2轮）

创造目标：用自己的登录 cookie 连接，auth 消息声明目标用户 ID。
如果服务端信任消息声明身份（或与 cookie 身份合并）→ 拿到目标用户视角数据。

构造：登录 cookie + auth userId=目标用户 + WS URL userId=目标用户。

对照组（判断标准：authSuccess 回显身份 + 视图数据）：
  1. cookie + userId=null（声明匿名，看服务端是否回退到 cookie 身份）
  2. cookie + userId=目标用户 1484993095538571712（身份叠加）
  3. cookie + userId=自己的 1666382703778278399（基准，应正常）

订阅：CurrentTeamCombinedPermissions（目标团队）+ FileBrowserSidebarData（目标团队）
"""
import json, sys, time, urllib.parse
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
COOKIE_STR = "; ".join(f"{c['name']}={c['value']}" for c in SESS if c.get("name") and c.get("value"))

WS_URL_ANON = open(r"D:\scan\_figma_hunt\ws_url_anon.txt").read().strip()
TARGET_TEAM = "1484993099407069875"
TARGET_USER = "1484993095538571712"
SELF_USER = "1666382703778278399"
HASH_PERMS = "f25ed3eceb859f73d4484895786b72fcf082f473c83967f96136f7fa8d0f05b4"      # CurrentTeamCombinedPermissions
HASH_SIDEBAR = "19ed18eb5eb008405731df268690983f08e7e9c314cb5d8b09b48da403b3548c"    # FileBrowserSidebarData
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


def run_case(name, user_id, url_user=None, wait=10):
    print(f"\n===== 测试: {name} (auth userId={user_id}, url userId={url_user}) =====")
    url = WS_URL_ANON
    if url_user:
        url = url.replace("userId=", f"userId={url_user}").replace("anonUserId=", f"anonUserId={url_user}")
    ws = websocket.create_connection(url, timeout=20,
                                     origin="https://www.figma.com",
                                     header=["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                                             f"Cookie: {COOKIE_STR}"])
    ws.send(json.dumps(auth_msg(user_id)))
    time.sleep(2)
    subs = [
        ("CurrentTeamCombinedPermissions", HASH_PERMS, {"teamId": TARGET_TEAM}),
        ("FileBrowserSidebarData", HASH_SIDEBAR, {"teamId": TARGET_TEAM}),
    ]
    for vn, vh, args in subs:
        ws.send(json.dumps(subscribe(vn, vh, args)))
        print("SENT:", vn, json.dumps(args, ensure_ascii=False))

    end = time.time() + wait
    seen = set()
    while time.time() < end:
        try:
            ws.settimeout(min(3, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode != 0x1:
                continue
            msg = json.loads(data)
            mt = msg.get("messageType")
            if mt == "authSuccess":
                print("  >>> authSuccess:", json.dumps(msg, ensure_ascii=False)[:250])
            elif mt in ("denormalizedPendingMutations", "viewLoaded"):
                text = json.dumps(msg, ensure_ascii=False)
                vn = msg.get("viewName") or list(msg.get("mutations", {}).keys())[0] if isinstance(msg.get("mutations"), dict) else mt
                key = vn + "|" + mt
                if key not in seen:
                    seen.add(key)
                    print(f"  [{mt}] {vn} 字节={len(text)}")
                    # 打印前 600 字符看内容
                    print("      ", text[:600])
        except websocket.WebSocketTimeoutException:
            continue
        except Exception as e:
            print("  recv err:", e)
            break
    ws.close()


if __name__ == "__main__":
    cases = [
        ("cookie+声明匿名", None, None),
        ("cookie+声明目标用户", TARGET_USER, None),
        ("cookie+声明目标用户+URL参数", TARGET_USER, TARGET_USER),
        ("cookie+声明自己（基准）", SELF_USER, None),
    ]
    for name, uid, url_uid in cases:
        try:
            run_case(name, uid, url_uid)
        except Exception as e:
            print(f"  FAIL: {e}")
