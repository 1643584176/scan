"""内容级 view 跨账号测试:B 会话订阅 A 私有文件 vs 自己文件
覆盖:ResolvedComments / FileWithCommentsAndReactions / ComponentUpdatesForFile /
      StateGroupUpdatesForFile / LibraryData
"""
import sys, json, asyncio, io, re
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
B_UID = "1667396392129259941"
A_F2 = "qzDqStIDJyGbthpKiuvfwg"
B_F = "xFETb3KJ8wh2U8wjD9jJeY"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

VIEWS = [
    ("ResolvedComments", "a1cf406e0c93591363e16d1a2fffa9a5913f2883d6530681d619a623ef2e6d5a"),
    ("FileWithCommentsAndReactions", "f8a9f1559e2f6f626ada9312cc6d6aab7ab93159c85c1d913602ffa44098befb"),
    ("ComponentUpdatesForFile", "ce0fab2c340a93161f5ef44d2832eb83886d6af8cf488f4d484be472d049b1a7"),
    ("StateGroupUpdatesForFile", "2de78467d59a4d6df8958733b67a21de63c9cb483bc7b8a5ff048197f0b4d6b1"),
    ("LibraryData", "fce68eeee3014e622a2b8b96ed5d952b6fd4d24158900c3bb2dc838fb0c84136"),
]

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

async def sub_view(view_name, vhash, fk, wait=10):
    frames = []
    try:
        async with websockets.connect(lg_url(B_UID, fk),
                                      additional_headers={"User-Agent": UA, "Cookie": CK_B,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(B_UID, fk)))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": vhash, "loadType": "initial",
                                      "args": {"fileKey": fk}}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str) and "denormalizedPendingMutations" in msg:
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        return [f"ERROR {type(e).__name__}: {str(e)[:90]}"]
    return frames

def summarize(frames):
    if not frames:
        return "无帧"
    total = sum(len(f) for f in frames)
    # 找关键字段
    found = set()
    for f in frames:
        for m in re.finditer(r'"fieldName":"([^"]+)","value":(\{[^}]{0,120}|\"[^\"]{0,80}\")', f):
            found.add(f"{m.group(1)}={m.group(2)[:80]}")
    head = []
    for f in frames[:1]:
        # 提取 initial/error
        for m in re.finditer(r'"initial":(\{[^}]{0,150})|"error"[^,}]{0,80}', f):
            head.append(m.group(0)[:150])
    return f"{len(frames)}帧/{total}B | 字段: " + "; ".join(list(found)[:6]) + " | " + "; ".join(head[:3])

async def main():
    for vname, vhash in VIEWS:
        print(f"\n===== {vname} =====")
        await asyncio.sleep(3)
        fa = await sub_view(vname, vhash, A_F2)
        print(f"  [B→A私有] {summarize(fa)}")
        await asyncio.sleep(3)
        fb = await sub_view(vname, vhash, B_F)
        print(f"  [B→自己]  {summarize(fb)}")
        # 对比:越权面有内容而基线没有 → 红旗
        sa, sb = summarize(fa), summarize(fb)
        if "无帧" not in sa and "无帧" in sb:
            print(f"  ⚠️ 红旗:B→A 有数据而 B→自己 无 → 检查原始帧!")
            for f in fa[:2]:
                print("    🖼", f[:800])
        elif "无帧" not in sa and "无帧" not in sb:
            print(f"  ⚠️ 双面都有数据 → 需人工比对内容是否不同")

asyncio.run(main())
