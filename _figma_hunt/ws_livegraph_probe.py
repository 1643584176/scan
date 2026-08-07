"""livegraph WS 测试（用户提供的抓包 URL 为确定性来源）

原始 URL:
wss://www.figma.com/api/livegraph?pv=1&pr=e5b828076698c1d9&pt=1786081987
&ph=9xNUKy_inuuDiWuwhw6JnjwpvMtdcdgfBBpeeeunrp0&userId=1666382703778278399
&anonUserId=09725c80-4313-4749-9eda-a73821e1496e&clientType=web
&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48
&preload={"CurrentTeamCombinedPermissions":{"hash":"f25ed3eceb859f73d4484895786b72fcf082f473c83967f96136f7fa8d0f05b4","args":{"teamId":"1666382706663462213"}}}
&requestedProtocolVersion=2&clientUrl=https://www.figma.com/design/qzDqStIDJyGbthpKiuvfwg/...
&connectionType=initial&reconnect=0

创造目标：
  1. preload.teamId 是否被信任（改 teamId → 是否返回该团队权限数据）
  2. preload.hash 是否被校验（改 hash → 是否仍 200/数据）
  3. 匿名 vs 登录
  4. pr/pt/ph token 是否绑定文件/用户
"""
import json, sys, time, base64
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
COOKIE = "; ".join(f"{c['name']}={c['value']}" for c in SESS if c.get("name") and c.get("value"))

TEAM = "1666382706663462213"
OTHER_TEAM = "1484993099407069875"   # 公开文件 Xi He 的 team
GHOST_TEAM = "9999999999999999999"

PR = "e5b828076698c1d9"
PT = "1786081987"
PH = "9xNUKy_inuuDiWuwhw6JnjwpvMtdcdgfBBpeeeunrp0"
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
USER = "1666382703778278399"
ANON = "09725c80-4313-4749-9eda-a73821e1496e"


def preload(team_id, hash_val=None):
    h = hash_val or "f25ed3eceb859f73d4484895786b72fcf082f473c83967f96136f7fa8d0f05b4"
    return base64.b64encode(json.dumps({"CurrentTeamCombinedPermissions": {"hash": h, "args": {"teamId": team_id}}}).encode()).decode()


def build(team_id, hash_val=None, use_cookie=False, pr=PR, pt=PT, ph=PH, user=USER):
    u = (f"wss://www.figma.com/api/livegraph?pv=1&pr={pr}&pt={pt}&ph={ph}"
         f"&userId={user}&anonUserId={ANON}&clientType=web&commitHash={COMMIT}"
         f"&preload={preload(team_id, hash_val)}"
         f"&requestedProtocolVersion=2"
         f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Fdesign%2FqzDqStIDJyGbthpKiuvfwg%2Ftest"
         f"&connectionType=initial&reconnect=0")
    return u, use_cookie


def test(name, team_id, hash_val=None, use_cookie=False, pr=PR, pt=PT, ph=PH, user=USER, wait=8):
    url, ck = build(team_id, hash_val, use_cookie, pr, pt, ph, user)
    headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"]
    if ck:
        headers.append(f"Cookie: {COOKIE}")
    try:
        ws = websocket.create_connection(url, timeout=15, origin="https://www.figma.com", header=headers)
    except Exception as e:
        print(f"  {name}: 握手失败 {type(e).__name__}: {e}")
        return
    got = 0
    msgs = []
    closed = False
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(2, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode == 0x8:
                closed = True
                break
            if opcode == 0x2:
                got += len(data)
                if len(msgs) < 5:
                    msgs.append(data[:200])
        except websocket.WebSocketTimeoutException:
            continue
        except Exception:
            closed = True
            break
    ws.close()
    print(f"  {name}: {'CLOSE' if closed else '保持'}, 数据 {got}B")
    for m in msgs:
        try:
            print(f"     msg: {m.decode(errors='replace')[:180]}")
        except Exception:
            print(f"     msg(bin): {m[:80].hex()}")


if __name__ == "__main__":
    print("=== 1. 原始 URL 基准 ===")
    test("原始team 匿名", TEAM)
    test("原始team 登录", TEAM, use_cookie=True)

    print("\n=== 2. teamId 篡改（hash 不变） ===")
    test("其他team(Xi He) 登录", OTHER_TEAM, use_cookie=True)
    test("ghost team 登录", GHOST_TEAM, use_cookie=True)
    test("其他team 匿名", OTHER_TEAM)

    print("\n=== 3. hash 篡改 ===")
    test("ghost hash 登录", TEAM, hash_val="f" * 64, use_cookie=True)
    test("ghost hash 匿名", TEAM, hash_val="f" * 64)

    print("\n=== 4. pr/pt/ph token 篡改 ===")
    test("pr篡改 登录", TEAM, use_cookie=True, pr="a" * 16)
    test("pt篡改 登录", TEAM, use_cookie=True, pt="0")
    test("ph篡改 登录", TEAM, use_cookie=True, ph="a" * 44)
