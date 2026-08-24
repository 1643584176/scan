# -*- coding: utf-8 -*-
"""第九轮: 批量公开文件 tier 扫描 -> pro/enterprise plan -> Admin 系列 404 语义确认
目标: 1) 找出所有非 starter 的公开 plan
     2) 对每个 pro/enterprise plan 跑 AdminRequestDashboardView
     3) 判定 404 = "无请求记录"(普遍) vs "plan 不支持"(个别)
"""
import sys, json, io, asyncio, time, urllib.parse, uuid, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import websockets

B_UID = "1667396392129259941"
A_MAKE = "5zb5YkoxMa09KpqOyuLcHD"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

FILE_KEYS = [
    "ucha7bf05fJ81CJZVoruo0",  # Flowbite pro team (已测 404)
    "CYs4jJGyYeUxpAVcJ2EAZ4",  # Material 3 (starter)
    "bv2nMIdFf4u3dESGail4sm",  # Figma Demo Org (enterprise org)
    "vU5NGHCW6Wc42ojtcAsaik",
    "vtTXyIEof8A3ATUvtvUGVm",
    "KaKIakOIfbwGangSQknMGn",
    "QDKl0fwEtUUZsaeVwfquBr",
    "kbKhOEtojLYuCxVM7vDhpX",
    "NZicFoZQKbFQlE4Kg8D7N9",
    "VRTXP8mnIln1FGL2RjkTSD",
    "W8GEdfgjJaZ21YbP4exVxr",
]


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

OUT = io.open("_ws_resolver_bypass_out9.txt", "w", encoding="utf-8")


def lg_url(fk, uid):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")


async def sub(view, args, fk, wait=8):
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


async def main():
    print("=== 1) 批量 tier 扫描 ===")
    plans = []  # (fileKey, parent_id, parent_type, tier)
    for fk in FILE_KEYS:
        frames = await sub("PlanByFileKey", {"fileKey": fk}, fk, wait=7)
        txt = " ".join(frames)
        tier = re.search(r'"tier":"([^"]*)"', txt)
        pid = re.search(r'"planParentId":"([^"]*)"', txt)
        ptype = re.search(r'"planParentType":"([^"]*)"', txt)
        t = tier.group(1) if tier else "?"
        p = pid.group(1) if pid else "?"
        ty = ptype.group(1) if ptype else "?"
        line = f"[PlanByFileKey] {fk[:12]}... tier={t} parent={ty}:{p}"
        print(line)
        OUT.write(line + "\n")
        if t in ("pro", "enterprise", "org") and p != "?":
            plans.append((fk, p, t))
        await asyncio.sleep(0.5)

    print(f"\n=== 2) 非 starter plan -> AdminRequestDashboardView ===")
    for fk, pid, tier in plans:
        args = {"planType": "Team", "planId": pid, "sortOrder": "DESC",
                "filterParams": "{}", "firstPageSize": 25, "__requestId": str(uuid.uuid4())}
        frames = await sub("AdminRequestDashboardView", args, fk, wait=9)
        txt = " ".join(frames)
        m = re.search(r'Status code = (\d+). Error message = .*?"message":"([^"]*)"', txt)
        has_data = any('"initial":{' in f and '"initial":{}' not in f for f in frames)
        if has_data:
            tag = "⭐返回数据"
            print(f"[AdminDash] {fk[:12]}... plan={tier}:{pid} -> ⭐ 返回数据!")
            for f in frames:
                if '"initial":{' in f and '"initial":{}' not in f:
                    print(f"  🖼 {f[:1000]}")
        elif m:
            tag = f"{m.group(1)} {m.group(2)}"
            print(f"[AdminDash] {fk[:12]}... plan={tier}:{pid} -> {tag}")
        else:
            tag = "其他/空壳"
            print(f"[AdminDash] {fk[:12]}... plan={tier}:{pid} -> {tag}")
        OUT.write(f"[AdminDash] {fk} plan={tier}:{pid} -> {tag}\n")
        for f in frames:
            OUT.write(f"  {f[:1200]}\n")
        await asyncio.sleep(0.5)

    OUT.close()


asyncio.run(main())
