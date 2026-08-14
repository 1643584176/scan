"""Plan 下游视图匿名探测：用 A 的 planRecordId + teamId 测 billing/项目/用户组/AI用量面
A_plan_record_id = cc6b6125-a07f-4d39-a54c-50ef65f33919 (uuid, 匿名从 TeamByIdForPlanView 拿到)
A_team_id = 1666382706663462213 (bigint)
"""
import sys, json, asyncio
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_PLAN = "cc6b6125-a07f-4d39-a54c-50ef65f33919"
A_TEAM = "1666382706663462213"
PUB_FILE = "bv2nMIdFf4u3dESGail4sm"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def lg_url():
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{PUB_FILE}"
            f"&connectionType=initial&reconnect=0")

async def sub(label, view_name, args, wait=12):
    frames = []
    try:
        async with websockets.connect(lg_url(),
                                      additional_headers={"User-Agent": UA,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": None, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": f"https://www.figma.com/file/{PUB_FILE}"},
                                      "clientRequestedVersion": 2}))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": "f" * 32, "loadType": "initial", "args": args}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str):
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}"); return
    data_frames = [f for f in frames if "computations" in f and '"computations":{}' not in f
                   or ('"initial":{' in f and '"initial":{}' not in f)]
    print(f"[{label}] 帧数={len(frames)} 有数据帧={len(data_frames)}")
    for f in data_frames:
        print(f"    🖼 {f[:800]}")
    if not data_frames:
        for f in frames[:2]:
            print(f"    · {f[:300]}")

async def main():
    tests = [
        ("Y8 续费确认", "PlanRenewalConfirmationView", {"planId": A_PLAN}),
        ("Y9 共享容器设置", "PlanSharedContainerSettingsView", {"planId": A_PLAN}),
        ("Y6 用户组存在性", "PlanHasUserGroups", {"planId": A_PLAN}),
        ("YJ AI用量月度", "PlanAiUsageMonthly", {"planId": A_PLAN, "sampleUserCount": 5}),
        ("Z7 用户组列表", "UserGroupsByPlan", {"planId": A_PLAN, "firstPageSize": 20}),
        ("Y4 连接项目", "PlanConnectedProjectsForPlanUser", {"planId": A_TEAM, "planType": "team"}),
        ("Y5 plan详情", "PlanCanConnectView", {"planParentId": A_TEAM, "planType": "team"}),
        ("Y3 planPublicInfo", "PlanIsConnectEnabled", {"planParentId": A_TEAM, "planType": "team"}),
    ]
    for label, name, args in tests:
        await sub(label, name, args)

asyncio.run(main())
