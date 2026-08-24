# -*- coding: utf-8 -*-
"""候选2: AiMeterUsageView 跨文件 AI 用量 (fileKey 参数注入)
B 订阅 A 文件的 AI 计量视图 -> 若返回 A 的 aiMeterUsage (含 userActions 用户操作记录) = 跨文件泄露
矩阵:
  1. 纯净 A 订阅 A 文件   -> 基线
  2. 纯净 B 订阅 A 文件   -> 核心!
  3. 纯净 A 订阅 B 文件   -> 反向
  4. 匿名 订阅 A 文件     -> 对照
"""
import sys, json, io, asyncio, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
B_FILE = "xFETb3KJ8wh2U8wjD9jJeY"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"


def clean_json_cookie_field(raw_value, keep_uid):
    v = urllib.parse.unquote(raw_value) if False else raw_value
    import urllib.parse
    v = urllib.parse.unquote(raw_value)
    try:
        d = json.loads(v)
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    nd = {k: val for k, val in d.items() if k == keep_uid}
    if not nd:
        return None
    return urllib.parse.quote(json.dumps(nd, separators=(",", ":")))


def make_abs_pure(cookie, keep_uid):
    import urllib.parse
    parts = {}
    for p in cookie.split("; "):
        if "=" in p:
            k, v = p.split("=", 1)
            parts[k] = v
    authn_raw = parts.get("__Host-figma.authn", "")
    d = json.loads(urllib.parse.unquote(authn_raw))
    d = {k: v for k, v in d.items() if k == keep_uid}
    parts["__Host-figma.authn"] = urllib.parse.quote(json.dumps(d, separators=(",", ":")))
    if "__Host-figma.embed" in parts:
        ne = clean_json_cookie_field(parts["__Host-figma.embed"], keep_uid)
        if ne:
            parts["__Host-figma.embed"] = ne
        else:
            del parts["__Host-figma.embed"]
            parts.pop("__Host-figma.embed.mac", None)
    return "; ".join(f"{k}={v}" for k, v in parts.items())


rawB = io.open("ws_cookie_B_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
rawA = io.open("ws_cookie_A_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
ABS_A = make_abs_pure(rawA, A_UID)
ABS_B = make_abs_pure(rawB, B_UID)


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def probe(label, cookie, uid, fk):
    frames = []
    try:
        async with websockets.connect(lg_url(fk, uid),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": uid, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": f"https://www.figma.com/file/{fk}"},
                                      "clientRequestedVersion": 2}))
            au = None
            for _ in range(3):
                m = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(m, str) and "authSuccess" in m:
                    au = json.loads(m).get("userId")
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "AiMeterUsageView",
                                      "viewHash": "f" * 32, "loadType": "initial",
                                      "args": {"fileKey": fk}}))
            deadline = time.time() + 12
            while time.time() < deadline:
                try:
                    m = await asyncio.wait_for(ws.recv(), timeout=3)
                except asyncio.TimeoutError:
                    continue
                if isinstance(m, str):
                    frames.append(m)
                    if "viewLoaded" in m:
                        break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}")
        return
    print(f"[{label}] authUserId={au} 帧数={len(frames)}")
    for f in frames:
        if "aiMeterUsage" in f or "bypassMetering" in f or "userActions" in f:
            print(f"  🖼 {f[:1200]}")
        elif "viewLoaded" in f or "error" in f.lower():
            print(f"  ℹ {f[:300]}")


async def main():
    print("=" * 70)
    print("1. 纯净 A 订阅 A 文件 (基线)")
    await probe("纯净A→A文件", ABS_A, A_UID, A_DESIGN)
    print("=" * 70)
    print("2. 纯净 B 订阅 A 文件 (核心!)")
    await probe("纯净B→A文件", ABS_B, B_UID, A_DESIGN)
    print("=" * 70)
    print("3. 纯净 B 订阅 A make 文件")
    await probe("纯净B→A_make", ABS_B, B_UID, A_MAKE)
    print("=" * 70)
    print("4. 纯净 A 订阅 B 文件 (反向)")
    await probe("纯净A→B文件", ABS_A, A_UID, B_FILE)
    print("=" * 70)
    print("5. 匿名订阅 A 文件 (对照)")
    await probe("匿名→A文件", "", "0", A_DESIGN)


asyncio.run(main())
