# -*- coding: utf-8 -*-
"""匿名对照：A_FILE 是否 linkAccess=view 设计行为
判据: 匿名也能通过 CalendarFileByKey/FileExpirationView 拿到 name → 设计行为, 非越权
     匿名拿不到但 B 拿到 → 需要进一步分析
"""
import sys, json, io, asyncio, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

A_UID = "1666382703778278399"
A_FILE = "u5aqDppy2y02845uEviKF5"      # A 私有? mention-test-a (linkAccess=view)
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"      # A 真正私有 (linkAccess=inherit)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
OUT = io.open("_ws_anon_control_out.txt", "w", encoding="utf-8")


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def sub(view, args, fk, uid, ck, wait=8):
    frames = []
    hdrs = {"User-Agent": UA, "Origin": "https://www.figma.com"}
    if ck:
        hdrs["Cookie"] = ck
    anon = uid == "anonymous"
    url_uid = "" if anon else uid
    try:
        async with websockets.connect(lg_url(fk, url_uid), additional_headers=hdrs,
                                      max_size=50_000_000, open_timeout=30) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": None if anon else uid, "anonymousUserId": None},
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
    OUT.write(f"\n===== [{label}] {view} -> {tag} =====\n")
    for f in frames:
        OUT.write(f"  {f[:1800]}\n")
    return tag


VIEWS = [
    ("CalendarFileByKey", lambda fk: {"fileKey": fk}),
    ("FileExpirationView", lambda fk: {"figFileKey": fk}),
    ("HasCollectionsView", lambda fk: {"fileKey": fk}),
]


async def main():
    print("=== 匿名 → A_FILE (linkAccess=view) ===")
    for name, mk in VIEWS:
        await run_case("匿名→A_FILE", name, mk(A_FILE), A_FILE, "anonymous", None)
    print("\n=== 匿名 → A_MAKE (linkAccess=inherit, 对照组) ===")
    for name, mk in VIEWS:
        await run_case("匿名→A_MAKE", name, mk(A_MAKE), A_MAKE, "anonymous", None)


asyncio.run(main())
OUT.close()
print("\n完成")
