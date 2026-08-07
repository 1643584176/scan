"""Figma multiplayer WS 对照测试

创造目标：找出 multiplayer 连接被服务端立即 CLOSE 的原因。
两种可能：权限拒绝（私有文件） vs 缺协议条件（所有文件都关）。

对照设计（判断标准：连接是否保持 + 是否收到业务消息）：
  1. 公开文件匿名           → 若能连：鉴权生效于权限层；若也关：缺握手条件
  2. 公开文件匿名+user-id   → 若 user-id 声明有效：身份参数可伪造
  3. 公开文件登录态         → 已知行为基线
  4. 私有文件登录态         → 复现用户环境（应保持连接）
  5. 私有文件匿名           → 若保持连接：私有文件内容泄露（高危）

URL 参数全部来自用户抓包（确定性来源），只替换 fileKey / user-id / 删减参数。
"""
import json, sys, time
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
COOKIE_STR = "; ".join(f"{c['name']}={c['value']}" for c in SESS if c.get("name") and c.get("value"))

PUBLIC = "bv2nMIdFf4u3dESGail4sm"
PRIVATE = "qzDqStIDJyGbthpKiuvfwg"
SELF = "1666382703778278399"
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


def test(name, url, cookie=False, wait=8):
    print(f"\n===== {name} =====")
    print(f"  {url}")
    headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"]
    if cookie:
        headers.append(f"Cookie: {COOKIE_STR}")
    try:
        ws = websocket.create_connection(url, timeout=15, origin="https://www.figma.com", header=headers)
        print("  握手成功 (101)")
    except Exception as e:
        print(f"  握手失败: {type(e).__name__} {e}")
        return
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(3, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode == 0x8:  # close 帧
                print(f"  >>> 服务端 CLOSE: {data!r}")
                return
            if opcode == 0x1:
                print(f"  [文本 {len(data)}B] {data[:400]}")
            elif opcode == 0x2:
                print(f"  [二进制 {len(data)}B]")
            elif opcode == 0x9:
                print("  [ping]")
        except websocket.WebSocketTimeoutException:
            continue
        except Exception as e:
            print(f"  连接中断: {type(e).__name__} {e}")
            return
    print("  连接保持 8s（无关闭）")
    ws.close()


if __name__ == "__main__":
    tests = [
        ("1.公开文件匿名", build_url(PUBLIC)),
        ("2.公开文件匿名+user-id=自己", build_url(PUBLIC, user_id=SELF)),
        ("3.公开文件登录态", build_url(PUBLIC), True),
        ("4.私有文件登录态(用户原样URL)", build_url(PRIVATE, user_id=SELF), True),
        ("5.私有文件匿名+user-id=自己", build_url(PRIVATE, user_id=SELF)),
    ]
    for name, *rest in tests:
        try:
            test(name, *rest)
        except Exception as e:
            print(f"  FAIL: {e}")
        time.sleep(1)
