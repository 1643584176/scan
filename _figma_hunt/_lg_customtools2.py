"""CustomTools 视图带 uid 重测(修正匿名问题)
OwnedCustomToolsView: 自己拥有的自定义工具
FileCustomToolsMetadataView: 文件引用的工具元数据
"""
import sys, json, asyncio, io, uuid
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
TARGET = "5Gs4PaTz11Hlk2sqVnidBG"   # A 的私有文件
PUBLIC = "bv2nMIdFf4u3dESGail4sm"   # 公开对照文件
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
FAKE_TOOL = str(uuid.uuid4())
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def lg_url(client_url, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")

def auth(client_url, uid):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": uid, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{client_url}"},
            "clientRequestedVersion": 2}

async def sub_view(label, view_name, args, cookie, client_url, uid, wait=12):
    frames = []
    try:
        async with websockets.connect(lg_url(client_url, uid),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(client_url, uid)))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    au = json.loads(msg).get("userId")
                    print(f"    [auth] userId={au}")
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": "00000000000000000000000000000000",
                                      "loadType": "initial", "args": args}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str) and ("denormalizedPendingMutations" in msg
                                                 or "errors" in msg and "view" in msg):
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}"); return
    total = sum(len(f) for f in frames)
    has_data = any('"initial": {' in f for f in frames)
    errs = [f for f in frames if '"errors"' in f and '"view"' in f]
    print(f"[{label}] 帧数={len(frames)} 总{total}B 含initial={has_data} 错误帧={len(errs)}")
    for f in frames:
        print(f"    🖼 {f[:600]}")

async def main():
    print("======== OwnedCustomToolsView ========")
    await sub_view("A→A owned", "OwnedCustomToolsView", {}, CK_A, TARGET, A_UID)
    await sub_view("B→B owned", "OwnedCustomToolsView", {}, CK_B, PUBLIC, B_UID)
    print("\n======== 越权: B→A owned / A→B owned ========")
    await sub_view("B→A owned", "OwnedCustomToolsView", {}, CK_B, TARGET, B_UID)
    await sub_view("A→B owned", "OwnedCustomToolsView", {}, CK_A, PUBLIC, A_UID)

    print("\n======== FileCustomToolsMetadataView ========")
    await sub_view("A→A 私有+假tool", "FileCustomToolsMetadataView",
                   {"fileKey": TARGET, "toolIds": [FAKE_TOOL]}, CK_A, TARGET, A_UID)
    await sub_view("B→A 私有+假tool", "FileCustomToolsMetadataView",
                   {"fileKey": TARGET, "toolIds": [FAKE_TOOL]}, CK_B, TARGET, B_UID)
    await sub_view("B→公开+假tool", "FileCustomToolsMetadataView",
                   {"fileKey": PUBLIC, "toolIds": [FAKE_TOOL]}, CK_B, PUBLIC, B_UID)

asyncio.run(main())
