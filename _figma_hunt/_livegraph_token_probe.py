# -*- coding: utf-8 -*-
"""livegraph realtime_token 利用 + 文件内容接口探测
1. B 用 A 的 realtime_token 连 livegraph 订阅 A 私有文件(FileView)
2. 抓 A 打开 design 文件时的内容加载请求(找文件内容接口)
"""
import io, json, sys, time, asyncio, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"


def load(path):
    return io.open(path, encoding='utf-8').read().strip().replace('\n', '; ')


BC = load('ws_cookie_B_new.txt')


def call(label, path, query=None, uid_hdr=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    if uid_hdr:
        headers["X-Figma-User-ID"] = uid_hdr
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:400]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:250]}")
        return e.code, raw


# 1. 拿 A 的 realtime_token(注入)
st, raw = call("拿A的realtime_token", f"/api/files/{A_DESIGN}/realtime_token",
               query={"fuid": A_UID})
tok = None
try:
    tok = json.loads(raw)["meta"]["realtime_token"]
except Exception:
    pass
print("realtime_token:", tok)

if tok:
    print("\n======== livegraph 用 A token 订阅 A 私有文件 ========")
    try:
        import websockets
        lg = (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
              f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds"
              f"&userId={B_UID}&anonUserId="
              f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
              f"&preload=%7B%7D&requestedProtocolVersion=2"
              f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{A_DESIGN}"
              f"&connectionType=initial&reconnect=0")

        async def try_sub(user_id, token):
            try:
                async with websockets.connect(lg, additional_headers={
                        "User-Agent": UA, "Cookie": BC, "Origin": BASE,
                        "X-Figma-Realtime-Token": token},
                        max_size=30_000_000, open_timeout=15) as ws:
                    auth = {"messageType": "auth", "clientType": "web",
                            "args": {"userId": user_id, "anonymousUserId": None},
                            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                     "clientUrl": "https://www.figma.com/files"},
                            "clientRequestedVersion": 2}
                    await ws.send(json.dumps(auth))
                    msgs = []
                    for _ in range(4):
                        try:
                            m = await asyncio.wait_for(ws.recv(), timeout=6)
                            msgs.append(str(m)[:400])
                        except asyncio.TimeoutError:
                            break
                    print(f"userId={user_id} msgs={len(msgs)}")
                    for m in msgs:
                        print("  ↳", m[:300])
            except Exception as e:
                print(f"userId={user_id} ❌ {type(e).__name__}: {str(e)[:120]}")

        # 尝试把 token 放入连接
        async def main():
            print("--- 尝试1: B userId + token header ---")
            await try_sub(B_UID, tok)
            print("--- 尝试2: A userId + token header ---")
            await try_sub(A_UID, tok)
        asyncio.run(main())
    except ImportError:
        print("websockets 未安装")

print("\n======== 文件内容接口探测(B+fuid=A) ========")
call("files key GET", f"/api/files/{A_DESIGN}?fuid={A_UID}&geometry=partial")
call("file content", f"/api/rest/v1/files/{A_DESIGN}?fuid={A_UID}")
call("node content", f"/api/rest/v1/files/{A_DESIGN}/nodes?ids=0%3A1&fuid={A_UID}")
