# GithubStatusView livegraph 测试
# 背景: githubAppStatus 前端走 livegraph view (figma_app 864950: o("GithubStatusView",["planId","planType"],"edd308789791a12f244f3b48ea6deb96cdac5b5ed82009db2399e9acdf329a98"))
# 目标: B 会话能否读到 A 的 GitHub 集成状态 (app_status / account_authorized / installation_id)
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_A = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip()
CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def lg_url(client_url):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId=&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")

def auth(client_url):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": None, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{client_url}"},
            "clientRequestedVersion": 2}

async def sub_view(label, args, cookie, client_url, view_hash="00000000000000000000000000000000", wait=12):
    frames = []
    try:
        async with websockets.connect(lg_url(client_url),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(client_url)))
            authed = False
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    authed = True
                    break
            print(f"[{label}] auth={'OK' if authed else 'FAIL?'} 发送 subscribe")
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "GithubStatusView",
                                      "viewHash": view_hash,
                                      "loadType": "initial", "args": args}))
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
    for i, f in enumerate(frames):
        print(f"--- 帧{i} ({len(f)}B) ---")
        print(f[:2500])

ARGS_A = {"planId": "1666382706663462213", "planType": "team"}   # A 的 team id (GitHub installation plan_id)
ARGS_A2 = {"planId": "cc6b6125-a07f-4d39-a54c-50ef65f33919", "planType": "team"}  # planRecord uuid 对照
# 真实 view hash 对照
H = "edd308789791a12f244f3b48ea6deb96cdac5b5ed82009db2399e9acdf329a98"

asyncio.run(sub_view("A基线 team_id", ARGS_A, CK_A, "5Gs4PaTz11Hlk2sqVnidBG"))
asyncio.run(sub_view("B→A team_id", ARGS_A, CK_B, "5Gs4PaTz11Hlk2sqVnidBG"))
asyncio.run(sub_view("A基线 plan_uuid", ARGS_A2, CK_A, "5Gs4PaTz11Hlk2sqVnidBG"))
asyncio.run(sub_view("B→A plan_uuid", ARGS_A2, CK_B, "5Gs4PaTz11Hlk2sqVnidBG"))
asyncio.run(sub_view("A基线 真实hash", ARGS_A, CK_A, "5Gs4PaTz11Hlk2sqVnidBG", view_hash=H))
asyncio.run(sub_view("B→A 真实hash", ARGS_A, CK_B, "5Gs4PaTz11Hlk2sqVnidBG", view_hash=H))
