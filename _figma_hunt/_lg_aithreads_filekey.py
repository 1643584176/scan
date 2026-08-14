"""FileAiChatThreadsView 正确参数重测:ownerId = 文件 key(非用户 id!)
关键测试:
1. A 登录 → A 私有文件 key → A 文件是否有 AI 线程
2. B 登录 → A 私有文件 key → 越权读 A 的 AI 线程(含对话内容 contentPb)⭐
3. 对照:匿名 → 公开文件 key(已知有线程 26586add-...)
"""
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_PRIV1 = "5Gs4PaTz11Hlk2sqVnidBG"   # A 私有文件 1
A_PRIV2 = "qzDqStIDJyGbthpKiuvfwg"   # A 私有文件 2
PUB = "bv2nMIdFf4u3dESGail4sm"       # Demo 公开文件(已知有线程)
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

async def sub_view(label, owner_id, cookie, uid, wait=12):
    frames = []
    fk = owner_id  # clientUrl 用同一个 key
    try:
        async with websockets.connect(lg_url(uid, fk),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(uid, fk)))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    au = json.loads(msg).get("userId")
                    print(f"    [auth] userId={au}")
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "FileAiChatThreadsView",
                                      "viewHash": "3ebe8bcd1ab2477b47769f9f4463b6541a104b6d6762402c7ffadd514bfbe08c",
                                      "loadType": "initial", "args": {"ownerId": owner_id}}))
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
    total = sum(len(f) for f in frames)
    has_data = any('"initial":{' in f for f in frames)
    errs = [f for f in frames if '"errors"' in f]
    print(f"[{label}] 帧数={len(frames)} 总{total}B 含initial={has_data} 错误帧={len(errs)}")
    shown = False
    for f in frames:
        if '"initial":{' in f and not shown:
            print(f"    📄 {f[:1800]}")
            shown = True
        elif '"initial":{' not in f and 'viewSubscriptionFailed' in f:
            print(f"    🚫 {f[:400]}")
    if not frames:
        print("    (无帧)")

async def main():
    print("======== FileAiChatThreadsView (ownerId=文件key) ========")
    # 1. A → A 私有文件 1(基线)
    await sub_view("A→A私有1 ⭐", A_PRIV1, CK_A, A_UID)
    # 2. A → A 私有文件 2
    await sub_view("A→A私有2 ⭐", A_PRIV2, CK_A, A_UID)
    # 3. B → A 私有文件 1(越权)⭐⭐
    await sub_view("B→A私有1 越权 ⭐⭐", A_PRIV1, CK_B, B_UID)
    # 4. B → A 私有文件 2(越权)⭐⭐
    await sub_view("B→A私有2 越权 ⭐⭐", A_PRIV2, CK_B, B_UID)
    # 5. 对照:B → 公开文件(应有线程)
    await sub_view("B→公开(对照)", PUB, CK_B, B_UID)

asyncio.run(main())
