# -*- coding: utf-8 -*-
"""PlanByFileKey -> Flowbite 公开文件: 完整打印 plan 字段(拿 planRecordId)
"""
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
B_UID = "1667396392129259941"
PUB = "ucha7bf05fJ81CJZVoruo0"   # Flowbite Design System Pro (pro 团队公开文件)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"


def lg_url(uid, fk):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def main():
    out = io.open("_flowbite_plan_dump.txt", "w", encoding="utf-8")
    try:
        async with websockets.connect(lg_url(B_UID, PUB),
                                      additional_headers={"User-Agent": UA, "Cookie": CK_B,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": B_UID, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": f"https://www.figma.com/file/{PUB}"},
                                      "clientRequestedVersion": 2}))
            for _ in range(3):
                m = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(m, str) and "authSuccess" in m:
                    print("auth ok")
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "PlanByFileKey",
                                      "viewHash": "00000000000000000000000000000000",
                                      "loadType": "initial", "args": {"fileKey": PUB}}))
            deadline = asyncio.get_event_loop().time() + 12
            while asyncio.get_event_loop().time() < deadline:
                try:
                    m = await asyncio.wait_for(ws.recv(), timeout=3)
                except asyncio.TimeoutError:
                    break
                if isinstance(m, str):
                    out.write(m + "\n")
                    if "planRecordId" in m or "stripeCustomerId" in m:
                        print(f"[+] {m[:400]}")
    except Exception as e:
        print(f"❌ {type(e).__name__}: {str(e)[:120]}")
    out.close()


asyncio.run(main())
