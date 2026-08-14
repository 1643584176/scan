"""LibraryKeyToFile 匿名订阅测试：
输入 community library_key，看返回 file.key 还是 hubFile.id"""
import sys, json, asyncio
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LIB_KEY = "lk-ccdecea2bd558996f2decf4d1c234c3bae9ff24a3764190bb5ab474e0ebef8e47fa78e3f65cf2158d711030f32975f25c24f78575f0cd6b2f948c86a0fe27955"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
CK_B = open('ws_cookie_B.txt', encoding='utf-8').read().strip()

def lg_url(client_url):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")

async def sub(label, cookie, wait=15):
    frames = []
    try:
        async with websockets.connect(lg_url("bv2nMIdFf4u3dESGail4sm"),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
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
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "LibraryKeyToFile",
                                      "viewHash": "a" * 32, "loadType": "initial",
                                      "args": {"libraryKey": LIB_KEY}}))
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
    print(f"[{label}] 帧数={len(frames)}")
    for f in frames:
        if '"initial":' in f or '"errors"' in f:
            print(f"    🖼 {f[:900]}")
    if not any('"initial":' in f for f in frames):
        for f in frames[:2]:
            print(f"    · {f[:400]}")

async def main():
    await sub("LibraryKeyToFile 匿名→community_lk", "")
    await sub("LibraryKeyToFile B→community_lk", CK_B)

asyncio.run(main())
