"""B 会话测 AI 线程/插件视图（ownerId/targetUserId 参数伪造）"""
import sys, json, asyncio
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK = open('cookie_header_new.txt', encoding='utf-8').read().strip()
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_ORG = "1666382706663462213"  # A team（org 未知，先用 team）
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
cat = json.load(open('lg_views_catalog.json', encoding='utf-8'))

def lg_url():
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2Fbv2nMIdFf4u3dESGail4sm"
            f"&connectionType=initial&reconnect=0")

AUTH = {"messageType": "auth", "clientType": "web",
        "args": {"userId": None, "anonymousUserId": None},
        "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                 "clientUrl": "https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm"},
        "clientRequestedVersion": 2}

CASES = [
    ("FileAiChatThreads ownerId=A", "FileAiChatThreadsView", {"ownerId": A_UID}),
    ("FileAiChatThreads ownerId=B", "FileAiChatThreadsView", {"ownerId": B_UID}),
    ("ActiveAiChatThread ownerId=A id=1", "ActiveAiChatThreadView", {"ownerId": A_UID, "id": 1}),
    ("PluginPrefs targetUser=A", "PluginPreferencesView", {"targetOrgId": A_ORG, "targetUserId": A_UID}),
    ("PluginPrefs targetUser=B", "PluginPreferencesView", {"targetOrgId": A_ORG, "targetUserId": B_UID}),
    ("AutoRunPlugins targetUser=A", "AutoRunPluginsView", {"targetOrgId": A_ORG, "targetUserId": A_UID}),
]

async def test_one(label, view_name, args, wait=12):
    vh = cat.get(view_name, {}).get("hash")
    if not vh:
        print(f"[{label}] 无hash"); return
    frames = []
    try:
        async with websockets.connect(lg_url(), additional_headers={"User-Agent": UA, "Cookie": CK, "Origin": "https://www.figma.com"}, max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(AUTH))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": vh, "loadType": "initial", "args": args}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str) and "denormalizedPendingMutations" in msg:
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}"); return
    total = sum(len(f) for f in frames)
    has_data = any('"initial": {' in f for f in frames)
    print(f"[{label}] 帧数={len(frames)} 总{total}B 含initial={has_data}")
    for f in frames:
        if '"initial": {' in f:
            print(f"    📄 {f[:400]}")
            break

async def main():
    for c in CASES:
        await test_one(*c)

asyncio.run(main())
