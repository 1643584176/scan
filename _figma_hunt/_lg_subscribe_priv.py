# -*- coding: utf-8 -*-
"""livegraph 订阅 A 私有文件内容视图(B cookie + A realtime_token)
订阅 FileView / FileUsersForFileView 等视图,验证能否读到设计内容
"""
import io, json, sys, asyncio, time
import websockets
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
A_THREAD = "ee5997d9-bbdb-4912-9587-9022c14c0be0"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
HASH = "ab" * 16


def lg_url(client_url="bv2nMIdFf4u3dESGail4sm"):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds"
            f"&userId={B_UID}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")


def auth():
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": B_UID, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": "https://www.figma.com/files"},
            "clientRequestedVersion": 2}


async def sub(label, view, args, wait=6):
    frames = []
    try:
        async with websockets.connect(lg_url(A_DESIGN),
                                      additional_headers={"User-Agent": UA, "Cookie": CK_B,
                                                          "Origin": BASE},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth()))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view,
                                      "viewHash": HASH, "loadType": "initial", "args": args}))
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
    hits = [f for f in frames if '"initial":' in f or 'viewSubscriptionFailed' in f or '"error"' in f]
    print(f"\n[{label}] 帧={len(frames)} 有效={len(hits)}")
    for f in hits[:3]:
        if 'viewSubscriptionFailed' in f or '"error"' in f:
            print(f"  🚫 {f[:400]}")
        else:
            print(f"  🖼 {len(f)}B {f[:900]}")
            print()


async def main():
    print("======== B 订阅 A 私有文件视图 ========")
    await sub("FileView 内容", "FileView", {"fileKey": A_DESIGN})
    await sub("FileUsersForFileView", "FileUsersForFileView", {"fileKey": A_DESIGN})
    await sub("FilePermissionsLgShadowView", "FilePermissionsLgShadowView",
              {"fileKey": A_DESIGN})


asyncio.run(main())
