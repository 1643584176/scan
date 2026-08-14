"""MCP 私有服务器批量扫描(此前只测过 A/B/Demo 3 个 plan)
对 11 个已知公开文件:PlanByFileKey 拿 planRecordId → McpConnectorsView 查 mcpServers/mcpClients
筛选 publishScope != public 的私有服务器(含 redactedCustomHeaders 等敏感配置)
"""
import sys, json, asyncio, io
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
B_UID = "1667396392129259941"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

FILE_KEYS = [
    "ucha7bf05fJ81CJZVoruo0",  # Flowbite pro team
    "CYs4jJGyYeUxpAVcJ2EAZ4",  # Material 3
    "bv2nMIdFf4u3dESGail4sm",  # Figma Demo Org
    "vU5NGHCW6Wc42ojtcAsaik",
    "vtTXyIEof8A3ATUvtvUGVm",
    "KaKIakOIfbwGangSQknMGn",
    "QDKl0fwEtUUZsaeVwfquBr",
    "kbKhOEtojLYuCxVM7vDhpX",
    "NZicFoZQKbFQlE4Kg8D7N9",
    "VRTXP8mnIln1FGL2RjkTSD",
    "W8GEdfgjJaZ21YbP4exVxr",
]

def lg_url(uid, fk):
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=251c5be83e6853e5&pt=1786072093"
            f"&ph=sb9dUg8LQV0WGY29b-j8nggmhGX8TR2vghWs-rNzbds&userId={uid}&anonUserId="
            f"&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload=%7B%7D&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Ffile%2F{fk}"
            f"&connectionType=initial&reconnect=0")

def auth(uid, fk):
    return {"messageType": "auth", "clientType": "web",
            "args": {"userId": uid, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": "81855c2bc7c604648169c4e4333f43579bfa7464",
                     "clientUrl": f"https://www.figma.com/file/{fk}"},
            "clientRequestedVersion": 2}

async def sub_once(view_name, args, fk, wait=8):
    frames = []
    try:
        async with websockets.connect(lg_url(B_UID, fk),
                                      additional_headers={"User-Agent": UA, "Cookie": CK_B,
                                                          "Origin": "https://www.figma.com"},
                                      max_size=50_000_000, open_timeout=15) as ws:
            await ws.send(json.dumps(auth(B_UID, fk)))
            for _ in range(3):
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, str) and "authSuccess" in msg:
                    break
            await ws.send(json.dumps({"messageType": "subscribe", "viewName": view_name,
                                      "viewHash": "00000000000000000000000000000000",
                                      "loadType": "initial", "args": args}))
            deadline = asyncio.get_event_loop().time() + wait
            while asyncio.get_event_loop().time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3)
                    if isinstance(msg, str) and "denormalizedPendingMutations" in msg:
                        frames.append(msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        return {"err": f"{type(e).__name__}: {str(e)[:80]}"}
    return frames

def extract_plan(frames):
    for f in frames:
        i = f.find('"planRecordId"')
        if i >= 0:
            m = f[i:i+60]
            rid = m.split('":"')[1].split('"')[0] if '":"' in m else None
            # 提取 plan id(team::x / organization::x)
            j = f.find('"id":"team::')
            pt = "team"
            if j < 0:
                j = f.find('"id":"organization::')
                pt = "org"
            pid = None
            if j >= 0:
                seg = f[j:j+80]
                pid = seg.split('::')[1].split('"')[0]
            return rid, pid, pt
    return None, None, None

async def main():
    print("======== MCP 私有服务器批量扫描(B 登录,11 公开文件) ========")
    plan_ids = {}
    for fk in FILE_KEYS:
        frames = await sub_once("PlanByFileKey", {"fileKey": fk}, fk)
        rid, pid, pt = extract_plan(frames)
        tag = "✅" if rid else "—"
        print(f"[PlanByFileKey] {fk[:12]}... {tag} planRecordId={rid} parent={pt}:{pid}")
        if rid:
            plan_ids[rid] = (fk, pid, pt)
        await asyncio.sleep(0.3)

    print("\n======== McpConnectorsView 扫描全部 planRecordId ========")
    for rid, (fk, pid, pt) in plan_ids.items():
        frames = await sub_once("McpConnectorsView", {"planId": rid}, fk, wait=10)
        txt = ""
        for f in frames:
            txt += f
        n_servers = txt.count('"publishScope"')
        n_clients = txt.count('"toolPreferences"')
        has_private = any(s for s in ["team", "org", "private"] if f'"{s}"' in txt and 'publishScope' in txt)
        print(f"[McpConnectors] plan={rid[:8]} parent={pt}:{pid} 服务器条目≈{n_servers} clients≈{n_clients} 含私有={has_private} 帧={len(frames)}")
        if n_servers or n_clients:
            for f in frames:
                if '"initial":{' in f:
                    print(f"    📄 {f[:1800]}")
                    break
        await asyncio.sleep(0.3)

asyncio.run(main())
