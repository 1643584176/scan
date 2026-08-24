# -*- coding: utf-8 -*-
"""PURE 无门控 view 批量探针：根 filter 无 dZ 绑定的 fileKey 类 view
基线: A 私有文件 (A_MAKE / mention-test-a)
跨用户: Flowbite 公开文件
判据: 基线有数据 + 跨用户也有数据(非公开数据) = 越权候选
"""
import sys, json, io, asyncio, time, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

A_UID = "1666382703778278399"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"      # A 私有 Make 文件
A_FILE = "u5aqDppy2y02845uEviKF5"      # A 私有 mention-test-a
FB_FILE = "ucha7bf05fJ81CJZVoruo0"     # Flowbite 公开文件(社区)
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
ABS_A = make_abs_pure(rawA, A_UID)
OUT = io.open("_ws_pure_probe_out.txt", "w", encoding="utf-8")


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


def has_data(frames):
    for f in frames:
        if '"initial":{' in f and '"initial":{}' not in f:
            return True
        if '"data":{' in f and '"data":{}' not in f:
            return True
    return False


def status_tag(frames):
    import re
    txt = " ".join(frames)
    m = re.search(r'Status code = (\d+). Error message = .*?"message":"([^"]*)"', txt)
    if m:
        return f"code={m.group(1)} msg={m.group(2)[:60]}"
    if has_data(frames):
        return "有数据"
    if any("Missing argument" in f or "argument error" in f for f in frames):
        return "参数错误"
    if "viewSubscriptionFailed" in txt:
        return "订阅失败"
    return "空壳"


async def run_case(label, view, args, fk):
    frames = await sub(view, args, fk, A_UID, ABS_A, wait=7)
    tag = status_tag(frames)
    print(f"[{label}] {view} -> {tag} 帧={len(frames)}")
    OUT.write(f"\n===== [{label}] {view} args={json.dumps(args)} -> {tag} =====\n")
    for f in frames:
        OUT.write(f"  {f[:1500]}\n")
    return tag


# view 参数构造
def fk_args(filekey, **extra):
    a = {"fileKey": filekey}
    a.update(extra)
    return a

VIEWS = [
    ("HasCollectionsView", lambda fk: fk_args(fk)),
    ("ListCollectionsView", lambda fk: fk_args(fk)),
    ("ListFieldSchemasView", lambda fk: fk_args(fk)),
    ("TestFileCmsCollectionsOrderView", lambda fk: fk_args(fk)),
    ("FileMakeVersionsView", lambda fk: fk_args(fk, firstPageSize=10)),
    ("FileFavoritedMakeVersionsView", lambda fk: fk_args(fk, firstPageSize=10)),
    ("GenericMakeCutoverStatusByFileKey", lambda fk: fk_args(fk)),
    ("WeaveEditLockView", lambda fk: fk_args(fk, cacheNonce="0")),
    ("WeaveFilePresenceView", lambda fk: fk_args(fk, cacheNonce="0")),
    ("SiteBundles", lambda fk: fk_args(fk)),
    ("SiteMount", lambda fk: fk_args(fk)),
    ("SitePublishDomainState", lambda fk: fk_args(fk)),
    ("WebFontsForFile", lambda fk: fk_args(fk)),
    ("FileWorkshopMode", lambda fk: fk_args(fk)),
    ("DeviceTryFileView", lambda fk: fk_args(fk)),
    ("FileExpirationView", lambda fk: {"figFileKey": fk}),
    ("CalendarFileByKey", lambda fk: fk_args(fk)),
    ("FileFeaturesEnabled", lambda fk: fk_args(fk)),
]


async def main():
    print("=== 第一轮: A 私有文件 (A_MAKE) ===")
    r1 = {}
    for name, mk in VIEWS:
        r1[name] = await run_case("A_MAKE", name, mk(A_MAKE), A_MAKE)
    print("\n=== 第二轮: Flowbite 公开文件 ===")
    for name, mk in VIEWS:
        r2 = await run_case("FB", name, mk(FB_FILE), FB_FILE)
        if r1.get(name) == "有数据" and r2 == "有数据":
            print(f"  >>> {name}: 双文件都有数据 - 检查数据是否含隐私")
        elif r1.get(name) == "有数据" and r2 != "有数据":
            print(f"  >>> {name}: A 有数据 FB 空壳 - 权限校验正常")


asyncio.run(main())
OUT.close()
print("\n完成")
