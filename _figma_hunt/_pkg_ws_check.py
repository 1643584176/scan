# -*- coding: utf-8 -*-
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
FILE_KEY = "bv2nMIdFf4u3dESGail4sm"

def lg_url():
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{FILE_KEY}"
            f"&connectionType=initial&reconnect=0")

def auth():
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": None, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{FILE_KEY}"},
            "clientRequestedVersion": 2}

async def main():
    try:
        async with websockets.connect(lg_url(),
                                      additional_headers={"User-Agent": UA, "Cookie": CK_A,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth()))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    print("auth OK"); break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName":
                "ComponentBrowserSettingsSidebarPackagesNavigationStackView",
                "viewHash": "00000000000000000000000000000000",
                "loadType": "initial", "args": {"fileKey": FILE_KEY}}))
            for _ in range(6):
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                if isinstance(msg, str) and "publishedPackages" in msg:
                    print("FOUND:", msg[:800])
                    return
                if isinstance(msg, str) and "error" in msg.lower():
                    print("ERR?", msg[:300])
    except Exception as e:
        print("FAIL", type(e).__name__, str(e)[:120])

asyncio.run(main())
