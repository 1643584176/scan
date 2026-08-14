"""PlanByFileKey → 公开文件:跨 org 读取 PlanSubscription(含 stripeCustomerId)完整字段重放
B 登录(非 Demo Org 成员)→ 公开文件 bv2nMIdFf4u3dESGail4sm → 完整打印所有响应帧
"""
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
B_UID = "1667396392129259941"
PUB = "bv2nMIdFf4u3dESGail4sm"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def lg_url(uid, fk):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")

def auth(uid, fk):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": uid, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{fk}"},
            "clientRequestedVersion": 2}

async def full_dump(label, file_key, cookie, uid, wait=15):
    frames = []
    try:
        async with websockets.connect(lg_url(uid, file_key),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(uid, file_key)))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    au = json.loads(msg).get("userId")
                    print(f"[{label}] auth userId={au}")
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "PlanByFileKey",
                                      "viewHash": "00000000000000000000000000000000",
                                      "loadType": "initial", "args": {"fileKey": file_key}}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str) and "denormalizedPendingMutations" in msg:
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}"); return
    print(f"[{label}] 帧数={len(frames)}")
    for i, f in enumerate(frames):
        print(f"--- 帧{i} ({len(f)}B) ---")
        print(f)
    print()

async def main():
    print("########## B(非成员) → Demo Org 公开文件 PlanByFileKey 完整重放 ##########")
    await full_dump("B→公开文件", PUB, CK_B, B_UID)

asyncio.run(main())
