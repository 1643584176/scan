"""批量匿名探测未测的高价值 livegraph 视图
目标:找到下一个像 PlanByFileKey 一样匿名可读的敏感视图"""
import sys, json, asyncio
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAT = json.load(open('lg_views_catalog.json', encoding='utf-8'))
PUB = "bv2nMIdFf4u3dESGail4sm"      # 公开文件(enterprise org)
ORG = "1484997479016537761"         # Figma Demo Org
TEAM = "1484993099407069875"        # PUB 文件团队
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

# (标签, 视图名, args)
TARGETS = [
    ("OrgByIdForPlanView",      "OrgByIdForPlanView",      {"orgId": ORG}),
    ("OrgByIdForPlanUserView",  "OrgByIdForPlanUserView",  {"orgId": ORG}),
    ("LibraryOrgSubscriptions", "LibraryOrgSubscriptions", {"orgId": ORG}),
    ("LibraryTeamSubscriptions","LibraryTeamSubscriptions",{}),
    ("LibraryPresetSubV2",      "LibraryPresetSubscriptionsV2", {"group": "default"}),
    ("TeamPermissions",         "TeamPermissions",         {"teamId": TEAM}),
    ("CurrentTeamCombPerms",    "CurrentTeamCombinedPermissions", {"teamId": TEAM}),
    ("FilePermissionsV2",       "FilePermissionsV2",       {"fileKey": PUB, "teamId": TEAM, "currentOrgId": None}),
    ("FileManagePermission",    "FileManagePermission",    {"fileKey": PUB}),
    ("StyleByKey",              "StyleByKey",              {"key": "196134914f1a2caaed0544fdf24c5dd5bc240d5e", "openFileKey": PUB}),
    ("VariableByKey",           "VariableByKey",           {"key": "019b20b56352f8679acd7aad132c690f2e6c545d"}),
    ("VariableCollectionByKey", "VariableCollectionByKey", {"key": "035e4ac9aca4a1d799d59f1397d4a2a0d258ad02"}),
    ("UserForRcs",              "UserForRcs",              {}),
    ("UserPreferences",         "UserPreferences",         {}),
    ("FileAiChatThreadsView",   "FileAiChatThreadsView",   {"ownerId": PUB}),
    ("ActiveAiChatThread",      "ActiveAiChatThreadView",  {"ownerId": PUB, "id": "26586add-d136-422a-a39b-df6fc226da56"}),
    ("ResolvedComments",        "ResolvedComments",        {"fileKey": PUB}),
    ("FileWithComments",        "FileWithCommentsAndReactions", {"fileKey": PUB}),
    ("SavedResources",          "SavedResources",          {"orgId": None}),
    ("AutoRunPluginsView",      "AutoRunPluginsView",      {"targetOrgId": ORG, "targetUserId": None}),
]

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

async def sub(label, view_name, args, wait=8):
    frames = []
    try:
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
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}")
        return
    total = sum(len(f) for f in frames)
    has_initial = any('"initial": {' in f for f in frames)
    has_comp = any('"computations": {' in f and '"fieldName"' in f for f in frames)
    print(f"[{label}] 帧数={len(frames)} 总{total}B initial={has_initial} computations={has_comp}")
    for f in frames[:3]:
        print(f"    🖼 {f[:500]}")

async def main():
    for label, vn, args in TARGETS:
        await sub(label, vn, args)
    print("\n=== 完成 ===")

asyncio.run(main())
