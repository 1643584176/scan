"""multiplayer role 参数矩阵测试

创造目标：role 参数决定服务端走哪条权限/数据路径。
如果某个 role（viewer/prototype/viewerWithCpp）的路径忘了文件权限判断 →
匿名 + 私有文件 + 该 role = 拿到私有场景图。

对照设计（判断标准：连接是否保持 + 数据量）：
  公开文件(公开)  x role∈{editor,viewer,prototype,viewerWithCpp}  基线
  私有文件(私有)  x role∈{editor,viewer,prototype,viewerWithCpp}  攻击面

另外测试 fuid 参数（JS 里 prototype 模式专用身份参数）：
  公开文件 + role=prototype + fuid=目标用户 → 若数据变化 = 身份参数生效
"""
import json, sys, time
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
COOKIE_STR = "; ".join(f"{c['name']}={c['value']}" for c in SESS if c.get("name") and c.get("value"))

PUBLIC = "bv2nMIdFf4u3dESGail4sm"
PRIVATE = "qzDqStIDJyGbthpKiuvfwg"
SELF = "1666382703778278399"
TARGET = "1484993095538571712"
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"

ROLES = ["editor", "viewer", "prototype", "viewerWithCpp"]


def build_url(file_key, role, user_id=None, fuid=None):
    u = (f"wss://www.figma.com/api/multiplayer/{file_key}"
         f"?role={role}"
         f"&tracking_session_id=bbenpPqP1cBhDyOD"
         f"&version=201&recentReload=0"
         f"&file-load-streaming-compression"
         f"&scenegraph-queries-initial-nodes=0:1")
    if user_id:
        u += f"&user-id={user_id}"
    if fuid:
        u += f"&fuid={fuid}"
    u += f"&client_release={COMMIT}"
    return u


def test(name, url, cookie=False, wait=6):
    headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/149.0.0.0 Safari/537.36"]
    if cookie:
        headers.append(f"Cookie: {COOKIE_STR}")
    try:
        ws = websocket.create_connection(url, timeout=15, origin="https://www.figma.com", header=headers)
    except Exception as e:
        print(f"  {name}: 握手失败 {type(e).__name__}")
        return
    got = 0
    closed = False
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(3, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode == 0x8:
                closed = True
                break
            if opcode == 0x2:
                got += len(data)
        except websocket.WebSocketTimeoutException:
            continue
        except Exception:
            closed = True
            break
    ws.close()
    status = "CLOSE" if closed else "保持"
    print(f"  {name}: {status}, 数据 {got}B")


if __name__ == "__main__":
    print("=== 公开文件 x role 矩阵（匿名） ===")
    for r in ROLES:
        test(f"公开 role={r}", build_url(PUBLIC, r))

    print("\n=== 私有文件 x role 矩阵（匿名） ===")
    for r in ROLES:
        test(f"私有 role={r}", build_url(PRIVATE, r))

    print("\n=== fuid 身份参数测试（匿名 + 公开文件 + prototype） ===")
    test("公开 prototype fuid=目标", build_url(PUBLIC, "prototype", fuid=TARGET))
    test("公开 prototype fuid=自己", build_url(PUBLIC, "prototype", fuid=SELF))

    print("\n=== 私有文件 role 变体（登录态对照） ===")
    test("私有 viewer 登录", build_url(PRIVATE, "viewer"), True)
    test("私有 prototype 登录", build_url(PRIVATE, "prototype"), True)
