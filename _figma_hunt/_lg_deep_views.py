"""深挖 4 个有信号的视图:保存完整帧,提取关键字段"""
import sys, json, asyncio, re
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAT = json.load(open('lg_views_catalog.json', encoding='utf-8'))
PUB = "bv2nMIdFf4u3dESGail4sm"
ORG = "1484997479016537761"
TEAM = "1484993099407069875"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

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

async def collect(label, view_name, args, wait=10):
    frames = []
    async with websockets.connect(lg_url(PUB),
                                  additional_headers={"User-Agent": UA, "Cookie": "",
                                                      "Origin": "https://www.figma.com"},
                                  max_size=50_000_000, open_timeout=15) as ws:
        await ws.send(json.dumps(auth(PUB)))
        for _ in range(3):
            msg = await asyncio.wait_for(ws.recv(), timeout=8)
            if isinstance(msg, str) and "authSuccess" in msg:
                break
        await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                  "viewHash": CAT[view_name]["hash"],
                                  "loadType": "initial", "args": args}))
        deadline = asyncio.get_event_loop().time() + wait
        while asyncio.get_event_loop().time() < deadline:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                if isinstance(msg, str) and "denormalizedPendingMutations" in msg:
                    frames.append(msg)
            except asyncio.TimeoutError:
                break
    return frames

def pretty(path, label, frames):
    out = [f"=== {label} ({len(frames)} 帧) ==="]
    for f in frames:
        # 提取所有 computations 的 fieldName/value 对
        comps = re.findall(r'"fieldName":"([^"]+)","value":([^}]{0,200})', f)
        for name, val in comps:
            out.append(f"  comp: {name} = {val[:180]}")
        # 提取 initial 的非空对象
        for m in re.finditer(r'"initial":\{"[^}]{10,}', f):
            out.append(f"  initial: {m.group(0)[:400]}")
    txt = '\n'.join(out)
    open(path, 'a', encoding='utf-8').write(txt + '\n\n')
    print(txt[:2500])

async def main():
    open('lg_deep_dive.txt', 'w', encoding='utf-8').write('')
    # 1. CurrentTeamCombinedPermissions — subscription 字段
    f = await collect("CTCP", "CurrentTeamCombinedPermissions", {"teamId": TEAM})
    pretty('lg_deep_dive.txt', "CurrentTeamCombinedPermissions(匿名)", f)
    # 2. OrgByIdForPlanView — planPublicInfo
    f = await collect("OBFPV", "OrgByIdForPlanView", {"orgId": ORG})
    pretty('lg_deep_dive.txt', "OrgByIdForPlanView(匿名)", f)
    # 3. FileAiChatThreadsView — AI 线程
    f = await collect("FACTV", "FileAiChatThreadsView", {"ownerId": PUB})
    pretty('lg_deep_dive.txt', "FileAiChatThreadsView(匿名)", f)
    # 4. FilePermissionsV2 — 完整 16 帧
    f = await collect("FPV2", "FilePermissionsV2", {"fileKey": PUB, "teamId": TEAM, "currentOrgId": None})
    pretty('lg_deep_dive.txt', "FilePermissionsV2(匿名)", f)

asyncio.run(main())
