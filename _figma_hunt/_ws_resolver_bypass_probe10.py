# -*- coding: utf-8 -*-
"""第十轮: team 级 view 重测(带 __requestId) — B 身份 + Flowbite pro teamId
目标: 找"无归属校验"的 team 级 view -> 列出他团队私有项目/文件/组件/字体
对照: B 自己的团队 (B_TEAM) 确认 view 正常工作
"""
import sys, json, io, asyncio, time, urllib.parse, uuid, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

B_UID = "1667396392129259941"
PRO_TEAM = "947922137358580288"   # Flowbite pro 团队
B_TEAM = "1667396394890946753"    # 对照: B 自己的 starter 团队
PRO_FILE = "ucha7bf05fJ81CJZVoruo0"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
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

OUT = io.open("_ws_resolver_bypass_out10.txt", "w", encoding="utf-8")


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def sub(view, args, fk, wait=9):
    frames = []
    try:
        async with websockets.connect(lg_url(fk, B_UID),
                                      additional_headers={"User-Agent": UA, "Cookie": ABS_B,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=30) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": B_UID, "anonymousUserId": None},
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


# (label, view, args) — Flowbite pro team
CASES = [
    ("FilesForTeam",          "FilesForTeam",
     {"teamId": PRO_TEAM, "updatedAtTimestamp": 0, "__requestId": str(uuid.uuid4())}),
    ("TeamProjectsPreview",   "TeamProjectsWithFilesPreview",
     {"teamId": PRO_TEAM, "__requestId": str(uuid.uuid4())}),
    ("LimitedTeamProjects",   "LimitedTeamProjectsWithFilesPreview",
     {"teamId": PRO_TEAM, "__requestId": str(uuid.uuid4())}),
    ("TeamSummary",           "TeamSummary",
     {"teamId": PRO_TEAM, "__requestId": str(uuid.uuid4())}),
    ("ColorPalettes",         "ColorPalettesForTeam",
     {"teamId": PRO_TEAM, "__requestId": str(uuid.uuid4())}),
    ("ComponentUpdates",      "ComponentUpdatesForTeam",
     {"teamId": PRO_TEAM, "__requestId": str(uuid.uuid4())}),
    ("FontFile",              "FontFileForTeamView",
     {"teamId": PRO_TEAM, "updatedAtTimestamp": 0, "__requestId": str(uuid.uuid4())}),
    ("FileViewHistory",       "FileViewHistoryExp",
     {"teamId": PRO_TEAM, "__requestId": str(uuid.uuid4())}),
    ("ActiveFileUsers",       "ActiveFileUsersForFileView",
     {"fileKey": PRO_FILE, "__requestId": str(uuid.uuid4())}),
    ("LibrarySubs",           "LibrarySubscriptionsForTeam",
     {"teamId": PRO_TEAM, "__requestId": str(uuid.uuid4())}),
]
# 对照: B 自己团队
CONTROL = [
    ("TeamSummary 对照B", "TeamSummary",
     {"teamId": B_TEAM, "__requestId": str(uuid.uuid4())}),
    ("FilesForTeam 对照B", "FilesForTeam",
     {"teamId": B_TEAM, "updatedAtTimestamp": 0, "__requestId": str(uuid.uuid4())}),
]


async def run_case(label, view, args):
    fk = A_MAKE if "fileKey" in args else A_MAKE
    frames = await sub(view, args, fk, wait=9)
    txt = " ".join(frames)
    has_data = any('"initial":{' in f and '"initial":{}' not in f for f in frames)
    m = re.search(r'Status code = (\d+). Error message = .*?"message":"([^"]*)"', txt)
    if has_data:
        tag = "⭐返回数据"
    elif m:
        tag = f"⚠{m.group(1)} {m.group(2)[:40]}"
    elif any("argument error" in f for f in frames):
        tag = "⚠参数错误"
    elif any("error" in f.lower() for f in frames):
        tag = "⚠有错误"
    else:
        tag = "空壳"
    print(f"[{label}] {tag} 帧数={len(frames)}")
    OUT.write(f"\n===== [{label}] {view} {tag} =====\n")
    for f in frames:
        OUT.write(f"  {f[:1800]}\n")
        if has_data and '"initial":{' in f and '"initial":{}' not in f:
            print(f"  🖼 {f[:1200]}")


async def main():
    print(f"第十轮: {len(CASES)} 个 Flowbite team 级 view + {len(CONTROL)} 个对照")
    for label, view, args in CASES:
        await run_case(label, view, args)
        await asyncio.sleep(0.4)
    print("--- 对照(B 自己团队) ---")
    for label, view, args in CONTROL:
        await run_case(label, view, args)
        await asyncio.sleep(0.4)
    OUT.close()


asyncio.run(main())
