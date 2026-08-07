"""multiplayer WS 跨用户连接测试：B(非协作者登录态) 连接 A 的私有文件

判断标准（连接是否保持 + 是否收到业务消息）：
  1. B + A私有文件 + role=editor    → 若保持且收到数据 = WS层越权
  2. B + A私有文件 + role=viewer    → viewer 角色对照
  3. B + A私有文件 + 伪装user-id=A  → user-id 参数是否被忽略（cookie 决定身份）
  4. B + B私有文件(自己)             → 基线：应正常连接
  5. A + A私有文件                   → owner 基线
  6. B + A公开文件                   → 公开文件对照（应能连）
URL 参数来自用户抓包（确定性来源），只替换 fileKey / user-id / cookie。
"""
import json, sys, time
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def load_cookie_str(f):
    return "; ".join(f"{c['name']}={c['value']}" for c in json.load(open(f, encoding="utf-8")) if c.get("name") and c.get("value"))

COOKIE_A = load_cookie_str("figma_session.json")       # A = owner
COOKIE_B = load_cookie_str("figma_session_new.json")   # B = 非协作者

A_PRIVATE = "qzDqStIDJyGbthpKiuvfwg"
B_PRIVATE = "aJ7MyOcCcwkIcoRzlMDEmH"
A_PUBLIC = "bv2nMIdFf4u3dESGail4sm"
UID_A = "1666382703778278399"
UID_B = "1667396392129259941"
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"


def build_url(file_key, user_id=None, role="editor"):
    u = (f"wss://www.figma.com/api/multiplayer/{file_key}"
         f"?role={role}"
         f"&tracking_session_id=bbenpPqP1cBhDyOD"
         f"&version=201&recentReload=0"
         f"&file-load-streaming-compression"
         f"&scenegraph-queries-initial-nodes=0:1")
    if user_id:
        u += f"&user-id={user_id}"
    u += f"&client_release={COMMIT}"
    return u


def test(name, url, cookie=None, wait=8):
    print(f"\n===== {name} =====")
    headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"]
    if cookie:
        headers.append(f"Cookie: {cookie}")
    try:
        ws = websocket.create_connection(url, timeout=15, origin="https://www.figma.com", header=headers)
        print("  握手成功 (101)")
    except Exception as e:
        print(f"  握手失败: {type(e).__name__} {str(e)[:200]}")
        return
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(3, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode == 0x8:
                print(f"  >>> 服务端 CLOSE: {data!r}")
                return
            if opcode == 0x1:
                print(f"  [文本 {len(data)}B] {data[:300]}")
            elif opcode == 0x2:
                print(f"  [二进制 {len(data)}B]")
            elif opcode == 0x9:
                print("  [ping]")
        except websocket.WebSocketTimeoutException:
            continue
        except Exception as e:
            print(f"  连接中断: {type(e).__name__} {str(e)[:150]}")
            return
    print("  连接保持（无关闭）")
    ws.close()


if __name__ == "__main__":
    tests = [
        ("1.B会话+A私有文件 role=editor", build_url(A_PRIVATE, user_id=UID_B), COOKIE_B),
        ("2.B会话+A私有文件 role=viewer", build_url(A_PRIVATE, user_id=UID_B, role="viewer"), COOKIE_B),
        ("3.B会话+A私有文件 伪装user-id=A", build_url(A_PRIVATE, user_id=UID_A), COOKIE_B),
        ("4.B会话+B私有文件(自己)", build_url(B_PRIVATE, user_id=UID_B), COOKIE_B),
        ("5.A会话+A私有文件(owner基线)", build_url(A_PRIVATE, user_id=UID_A), COOKIE_A),
        ("6.B会话+A公开文件", build_url(A_PUBLIC, user_id=UID_B), COOKIE_B),
    ]
    for name, url, ck in tests:
        try:
            test(name, url, ck)
        except Exception as e:
            print(f"  FAIL: {e}")
        time.sleep(1)
