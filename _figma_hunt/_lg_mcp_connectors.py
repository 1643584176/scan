"""McpConnectorsView(H7) 查询:A 基线 + B→A 越权
view: 1037 chunk H7={args:[planId], fields:{mcpServers:[id,name,url,transport,publishScope,redactedCustomHeaders...], mcpClients:[id,mcpServerId,toolPreferences...]}}
"""
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
PLAN_A = "1666382706663462213"   # A 的 team/plan id

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

async def sub_view(label, view_name, args, cookie, client_url, wait=12):
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
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}"); return
    print(f"[{label}] 帧数={len(frames)}")
    for f in frames:
        if 'denormalizedPendingMutations' in f or 'initial' in f or 'errors' in f:
            print(f"    🖼 {f[:1500]}")

async def main():
    print("======== McpConnectorsView 查询 ========")
    # 1. A 自身 plan(A cookie)
    await sub_view("A→A plan", "McpConnectorsView", {"planId": PLAN_A}, CK_A, "5Gs4PaTz11Hlk2sqVnidBG")
    # 2. B→A plan(越权)
    await sub_view("B→A plan", "McpConnectorsView", {"planId": PLAN_A}, CK_B, "5Gs4PaTz11Hlk2sqVnidBG")

asyncio.run(main())
