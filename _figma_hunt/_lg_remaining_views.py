"""回归 livegraph 剩余内容级 view:B 会话订阅 A 私有文件 vs 自己文件
筛选自 lg_views_catalog.json 中未测且接受 fileKey/key/figFileKey/branchFileKey/openFileKey 参数的 view
"""
import sys, json, asyncio, io, re
import websockets
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CK_B = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip()
B_UID = "1667396392129259941"
A_F2 = "qzDqStIDJyGbthpKiuvfwg"   # A 私有 design 文件
A_F1 = "5Gs4PaTz11Hlk2sqVnidBG"   # A 私有文件 2
B_F = "xFETb3KJ8wh2U8wjD9jJeY"    # B 自己文件
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36"

CAT = json.load(open('lg_views_catalog.json', encoding='utf-8'))

# 未测的内容级/状态级 view(接受文件 key 参数的)
VIEWS = [
    "OpenEditorFileData",
    "FileByKey",
    "PlanByFileKey",
    "FileWithRoleRequests",
    "FileEditRequestExistence",
    "LibraryFileSubscriptions",
    "LibraryModuleData",
    "LibraryVariableCollectionDataWithVariables",
    "LegacySourceStyleData",
    "HasCollectionsView",
    "ListCollectionsView",
    "WorkspaceSubscribedLibrariesForFile",
    "DeveloperRelatedLinks",
    "DeviceTryFileView",
    "BranchingPermissionsView",
    "CurrentWorkspaceView",
    "FileNameViewDropdown",
    "FileWorkshopMode",
    "FileExpirationView",
    "StarterFileEditConfirmation",
    "PreloadCodeConnectLk",
    # FileCan*/FileIs*/FileDevMode 权限布尔系列
    "FileCanAccessFullCodeConnect",
    "FileCanAccessFullDevMode",
    "FileCanAccessFullDevModeOrgPlus",
    "FileCanAccessMotionEntryPoint",
    "FileCanAccessTextureMode",
    "FileCanEdit",
    "FileCanEditAnnotations",
    "FileCanEditCmsContent",
    "FileCanExport",
    "FileCanUseAi",
    "FileCanUseAiOrDevModeAi",
    "FileCanUseAiOrViewerModeAi",
    "FileCanUseDevModeDemoFile",
    "FileCanUseFragmentSearchAi",
    "FileCanViewAnnotations",
    "FileCanViewAnnotationsMegadot",
    "FileDevModeTrialRequestPending",
    "FileIsEligibleForDevModeTrial",
    "FileIsInDevModeTrial",
]

# args 键名 -> 替换为文件 key 的映射(catalog 中 args 的键名)
KEY_ALIASES = ["fileKey", "key", "figFileKey", "branchFileKey", "openFileKey"]

def build_args(vname, fk):
    """按 catalog 的 args 结构,替换文件 key 相关字段,其余保持"""
    base = dict(CAT[vname].get("args") or {})
    for k in KEY_ALIASES:
        if k in base:
            base[k] = fk
    return base

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

async def sub_view(view_name, args, fk, wait=9):
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
                                      "viewHash": CAT[view_name]["hash"],
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
        return [f"ERROR {type(e).__name__}: {str(e)[:90]}"]
    return frames

def summarize(frames):
    if not frames:
        return "无帧"
    if frames[0].startswith("ERROR"):
        return frames[0]
    total = sum(len(f) for f in frames)
    # 提取 initial 数据段与字段
    fields = set()
    for f in frames:
        for m in re.finditer(r'"fieldName":"([^"]+)","value":(\{[^}]{0,100}|\[[^\]]{0,100}|"[^"]{0,60}"|true|false|null)', f):
            v = m.group(2)
            if len(v) > 80: v = v[:80] + "..."
            fields.add(f"{m.group(1)}={v}")
    # 检查是否有实体数据(entity/节点/评论等)
    dataish = re.findall(r'"(?:initial|data)":\{[^}]{0,60}', frames[0])
    return f"{len(frames)}帧/{total}B | " + "; ".join(list(fields)[:5]) + " | " + " ".join(dataish[:2])

async def main():
    for vname in VIEWS:
        if vname not in CAT:
            print(f"===== {vname} 不在 catalog,跳过 =====")
            continue
        print(f"\n===== {vname} =====")
        fa = await sub_view(vname, build_args(vname, A_F2), A_F2)
        sa = summarize(fa)
        print(f"  [B→A私有] {sa}")
        await asyncio.sleep(2)
        fb = await sub_view(vname, build_args(vname, B_F), B_F)
        sb = summarize(fb)
        print(f"  [B→自己]  {sb}")
        if "无帧" not in sa and "无帧" in sb:
            print(f"  ⚠️ 红旗:B→A 有数据而 B→自己 无!")
            for f in fa[:2]:
                print("    🖼", f[:900])
        elif "无帧" not in sa and "无帧" not in sb:
            # 双面都有数据,比较体积
            a_b = sum(len(f) for f in fa)
            b_b = sum(len(f) for f in fb)
            if a_b > b_b * 1.5:
                print(f"  ⚠️ 红旗:B→A({a_b}B) 显著大于 B→自己({b_b}B) → 检查!")
                for f in fa[:2]:
                    print("    🖼", f[:900])
        await asyncio.sleep(2)

asyncio.run(main())
