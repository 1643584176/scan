# -*- coding: utf-8 -*-
"""第二轮: 补齐缺失参数重测 B->A 管理 view(确认权限模型一致)
补参: sortOrder/filterParams/queryParams/meteringPeriodId(null尝试)
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
rawA = io.open("ws_cookie_A_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
ABS_B = make_abs_pure(rawB, B_UID)
ABS_A = make_abs_pure(rawA, A_UID)

CASES = [
    ("AccountTypeRequestsInPlan B->A",  "AccountTypeRequestsInPlan",
     {"planType": "Team", "planId": A_TEAM, "sortOrder": "DESC", "filterParams": "", "firstPageSize": 25}),
    ("AdminRequestDashboardView B->A",  "AdminRequestDashboardView",
     {"planType": "Team", "planId": A_TEAM, "sortOrder": "DESC", "filterParams": "", "firstPageSize": 25}),
    ("AdminNotificationsCount B->A",    "AdminNotificationsCountView",
     {"planType": "Team", "planId": A_TEAM, "filterParams": ""}),
    ("AdminRequestDashRowIds B->A",     "AdminRequestDashboardRowIds",
     {"planType": "Team", "planId": A_TEAM, "filterParams": ""}),
    ("OrgAdminUserView B->A",           "OrgAdminUserView",
     {"orgId": EXT_ORG, "queryParams": "{}", "firstPageSize": 25, "refetchToken": ""}),
    ("OrgAdminUserMinimal B->A",        "OrgAdminUserMinimalFieldsView",
     {"orgId": EXT_ORG, "queryParams": "{}", "firstPageSize": 25, "refetchToken": ""}),
    ("PlanAiUsageMonthly B->B(对照)",   "PlanAiUsageMonthly",
     {"planId": B_PLAN, "sampleUserCount": 25, "meteringPeriodId": None}),
    ("AccountTypeRequestsInPlan B->B",  "AccountTypeRequestsInPlan",
     {"planType": "Team", "planId": B_TEAM, "sortOrder": "DESC", "filterParams": "", "firstPageSize": 25}),
]

OUT = io.open("_ws_resolver_bypass_out2.txt", "w", encoding="utf-8")


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
    OUT.write(f"\n===== [{label}] {view} 帧数={len(frames)} =====\n")
    for f in frames:
        OUT.write(f"  {f[:1500]}\n")
        if "initial" in f and '"initial":{' in f and '"initial":{}' not in f:
            print(f"  🖼 {f[:700]}")
        elif "error" in f.lower():
            print(f"  ⚠ {f[:400]}")


async def main():
    print("A. B -> A 管理 view (补参)")
    for label, view, args in CASES[:6]:
        await probe(label, ABS_B, B_UID, view, args)
    print("B. B -> B 对照")
    for label, view, args in CASES[6:]:
        await probe(label, ABS_B, B_UID, view, args)
    print("C. A -> A 基线")
    await probe("AccountTypeRequestsInPlan A->A", ABS_A, A_UID, "AccountTypeRequestsInPlan",
                {"planType": "Team", "planId": A_TEAM, "sortOrder": "DESC", "filterParams": "", "firstPageSize": 25})
    OUT.close()


asyncio.run(main())
