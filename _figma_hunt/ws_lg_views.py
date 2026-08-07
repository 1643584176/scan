"""livegraph 高价值 view 匿名批量测试

FileByKey 权限正确，但 livegraph 520 个 view 各自实现权限——
其他 view 可能有判断遗漏。匿名订阅 + 私有/公开/其他team 对照。

view + args（JS 定义确定性来源）：
  DestinationProjectsForTeam        {teamId}
  FeedPostsByFileKey                {fileKey}
  FileByKeyThumbnailUrl             {fileKey}
  DesktopTabPreviewView             {fileKey}
  FileEditRequestExistence          {fileKey}
  FileBrowserProjectPageTitleView   {projectId}
  FileCreationPermissionsView       {projectId}
  DeveloperLinks                    {key}
  FavoriteResourceById              {resourceId, resourceType}
"""
import json, sys, time, base64, uuid
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
COOKIE = "; ".join(f"{c['name']}={c['value']}" for c in SESS if c.get("name") and c.get("value"))

PRIVATE = "qzDqStIDJyGbthpKiuvfwg"
PUBLIC = "bv2nMIdFf4u3dESGail4sm"
OTHER_TEAM = "1484993099407069875"
PRIVATE_FOLDER = "634606972"
PUBLIC_FOLDER = "355763952"
HASH = "f25ed3eceb859f73d4484895786b72fcf082f473c83967f96136f7fa8d0f05b4"

CASES = [
    # (view, args, 说明)
    ("DestinationProjectsForTeam", {"teamId": OTHER_TEAM}, "其他team项目列表"),
    ("DestinationProjectsForTeam", {"teamId": "1666382706663462213"}, "自己team项目列表(对照)"),
    ("FeedPostsByFileKey", {"fileKey": PRIVATE}, "私有文件动态"),
    ("FeedPostsByFileKey", {"fileKey": PUBLIC}, "公开文件动态(对照)"),
    ("FileByKeyThumbnailUrl", {"fileKey": PRIVATE}, "私有文件缩略图"),
    ("FileByKeyThumbnailUrl", {"fileKey": PUBLIC}, "公开文件缩略图(对照)"),
    ("DesktopTabPreviewView", {"fileKey": PRIVATE}, "私有文件标签预览"),
    ("DesktopTabPreviewView", {"fileKey": PUBLIC}, "公开文件标签预览(对照)"),
    ("FileEditRequestExistence", {"fileKey": PRIVATE}, "私有文件编辑请求"),
    ("FileBrowserProjectPageTitleView", {"projectId": PUBLIC_FOLDER}, "其他team项目标题"),
    ("FileBrowserProjectPageTitleView", {"projectId": PRIVATE_FOLDER}, "自己项目标题(对照)"),
    ("FileCreationPermissionsView", {"projectId": PUBLIC_FOLDER}, "其他team项目创建权限"),
    ("DeveloperLinks", {"key": PUBLIC}, "公开文件开发者链接"),
    ("DeveloperLinks", {"key": PRIVATE}, "私有文件开发者链接"),
    ("FavoriteResourceById", {"resourceId": PUBLIC, "resourceType": "FILE"}, "公开文件收藏状态"),
    ("FavoriteResourceById", {"resourceId": PRIVATE, "resourceType": "FILE"}, "私有文件收藏状态"),
]


def url_for():
    pre = base64.b64encode(json.dumps({"CurrentTeamCombinedPermissions": {"hash": HASH, "args": {"teamId": "1666382706663462213"}}}).encode()).decode()
    return (f"wss://www.figma.com/api/livegraph?pv=1&pr=e5b828076698c1d9&pt=1786081987&ph=9xNUKy_inuuDiWuwhw6JnjwpvMtdcdgfBBpeeeunrp0"
            f"&userId=1666382703778278399&anonUserId=09725c80-4313-4749-9eda-a73821e1496e&clientType=web&commitHash=5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
            f"&preload={pre}&requestedProtocolVersion=2"
            f"&clientUrl=https%3A%2F%2Fwww.figma.com%2Fdesign%2FqzDqStIDJyGbthpKiuvfwg%2Ftest&connectionType=initial&reconnect=0")


def sub(name, view, args, use_cookie=False, wait=5):
    headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"]
    if use_cookie:
        headers.append(f"Cookie: {COOKIE}")
    try:
        ws = websocket.create_connection(url_for(), timeout=15, origin="https://www.figma.com", header=headers)
    except Exception as e:
        print(f"  {name}: 握手失败 {type(e).__name__}")
        return None
    msg = {"messageType": "subscribe", "viewName": view, "viewHash": HASH,
           "loadType": "Initial", "args": args, "traceId": str(uuid.uuid4())}
    try:
        ws.send(json.dumps(msg))
    except Exception as e:
        print(f"  {name}: send 失败 {e}")
        ws.close()
        return None
    got = []
    closed = False
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(2, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode == 0x8:
                closed = True
                break
            if opcode in (1, 2):
                got.append(data)
        except websocket.WebSocketTimeoutException:
            continue
        except Exception:
            closed = True
            break
    ws.close()
    # 统计非 authSuccess 的数据
    data_msgs = [g for g in got if b"denormalized" in g or b"sync" in g or b"error" in g.lower()]
    total = sum(len(g) for g in got)
    print(f"  [{view}] {name}: {'CLOSE' if closed else '保持'}, {len(got)}条/{total}B, 数据消息{len(data_msgs)}条")
    for g in data_msgs[:2]:
        print(f"     {g.decode(errors='replace')[:350]}")
    return got


if __name__ == "__main__":
    print("=== livegraph 高价值 view 匿名测试 ===")
    for view, args, desc in CASES:
        print(f"\n--- {desc} ({view}) ---")
        sub(desc, view, args, use_cookie=False)
