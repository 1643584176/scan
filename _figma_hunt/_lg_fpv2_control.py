"""FilePermissionsV2 对照实验:
1. 匿名 vs B账号登录(公开文件) — 确认匿名拿到的数据是否越界
2. 匿名 → A私有文件 — 确认权限门
3. 匿名 → Flowbite(pro组织) — 确认跨组织通用性"""
import sys, json, asyncio, re
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAT = json.load(open('lg_views_catalog.json', encoding='utf-8'))
PUB = "bv2nMIdFf4u3dESGail4sm"
FLOWBITE = "ucha7bf05fJ81CJZVoruo0"
A_PRIV = "qzDqStIDJyGbthpKiuvfwg"
TEAM = "1484993099407069875"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
try:
    CK_B = open('ws_cookie_B.txt', encoding='utf-8').read().strip()
except Exception:
    CK_B = ''

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

async def collect(label, args, cookie, client_url, wait=12):
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
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "FilePermissionsV2",
                                      "viewHash": CAT["FilePermissionsV2"]["hash"],
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
        return []
    return frames

def analyze(label, frames):
    print(f"\n===== {label} ({len(frames)} 帧) =====")
    if not frames:
        return
    names = set()
    roles = set()
    invites = set()
    orgs = set()
    for f in frames:
        for m in re.finditer(r'"name":"([^"]{2,40})"', f):
            names.add(m.group(1))
        for m in re.finditer(r'"level":(\d+)[^}]{0,120}?"userId":"(\d+)"', f):
            roles.add(f"level={m.group(1)} userId={m.group(2)}")
        for m in re.finditer(r'"inviteeUserId":"(\d+)"[^}]{0,150}?"roleId":"(\d+)"', f):
            invites.add(f"invitee={m.group(1)} role={m.group(2)}")
        for m in re.finditer(r'"domain":"([^"]+)"[^}]{0,200}?"samlSsoOnlyAt":([^,}]{0,20})', f):
            orgs.add(f"domain={m.group(1)} samlSsoOnlyAt={m.group(2)}")
        for m in re.finditer(r'"googleSsoOnlyAt":([^,}]{0,30})', f):
            if m.group(1) != 'null':
                orgs.add(f"googleSsoOnlyAt={m.group(1)}")
    print(f"  泄露姓名: {sorted(names)}")
    print(f"  文件角色: {sorted(roles)[:10]}")
    print(f"  邀请记录: {sorted(invites)[:10]}")
    print(f"  Org域名/SSO: {sorted(orgs)[:5]}")
    for f in frames:
        if '"PlanSubscription"' in f:
            print("  含 PlanSubscription ✓")
        if '"OrgDomain"' in f:
            print("  含 OrgDomain ✓")
        if '"Invite"' in f:
            print("  含 Invite ✓")
        if '"GuestOrgUser"' in f:
            print("  含 GuestOrgUser ✓")
    total = sum(len(f) for f in frames)
    print(f"  总 {total}B")

async def main():
    # 1. 匿名 → 公开文件
    f = await collect("匿名→公开文件", {"fileKey": PUB, "teamId": TEAM, "currentOrgId": None}, "", PUB)
    analyze("匿名→公开文件(Demo Org)", f)
    # 2. B 登录 → 公开文件
    f = await collect("B登录→公开文件", {"fileKey": PUB, "teamId": TEAM, "currentOrgId": None}, CK_B, PUB)
    analyze("B登录→公开文件(Demo Org)", f)
    # 3. 匿名 → A 私有文件
    f = await collect("匿名→A私有文件", {"fileKey": A_PRIV, "teamId": None, "currentOrgId": None}, "", A_PRIV)
    analyze("匿名→A私有文件", f)
    # 4. 匿名 → Flowbite(pro 组织)
    f = await collect("匿名→Flowbite", {"fileKey": FLOWBITE, "teamId": None, "currentOrgId": None}, "", FLOWBITE)
    analyze("匿名→Flowbite(pro组织)", f)

asyncio.run(main())
