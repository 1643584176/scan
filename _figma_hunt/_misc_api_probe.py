# -*- coding: utf-8 -*-
"""未测接口候选: B(无注入) 视角
- team_role_requests: 读团队角色请求
- users/batched: 批量用户信息
- mcp/session_token_exchange: MCP 会话 token 交换
- buzz_approvals: 审批流
- subscriptions: 订阅信息
"""
import io, json, sys, urllib.error, urllib.parse, urllib.request
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = "https://www.figma.com"
A_UID = "1666382703778278399"
B_UID = "1667396392129259941"
A_TEAM = "1666382706663462213"
B_TEAM = "1667396394890946753"
A_DESIGN = "5Gs4PaTz11Hlk2sqVnidBG"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36"
BC = io.open('ws_cookie_B_new.txt', encoding='utf-8').read().strip().replace('\n', '; ')


def call(label, method, path, body=None, query=None):
    headers = {"User-Agent": UA, "Accept": "application/json", "Origin": BASE,
               "Referer": BASE + "/", "Cookie": BC}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    url = BASE + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read().decode(errors='replace')
            print(f"[{label}] HTTP {r.status} {raw[:280]}")
            return r.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors='replace')
        print(f"[{label}] HTTP {e.code} {raw[:280]}")
        return e.code, raw


print("===== 1. team_role_requests =====")
call("GET A team role_requests", "GET", "/api/team_role_requests", query={"team_id": A_TEAM})
call("GET B team role_requests", "GET", "/api/team_role_requests", query={"team_id": B_TEAM})
call("POST create role_request", "POST", "/api/team_role_requests",
     {"team_id": A_TEAM, "role": "editor"})

print("\n===== 2. users/batched =====")
call("users/batched A_UID", "GET", "/api/users/batched", query={"user_ids": A_UID})
call("users/batched B_UID", "GET", "/api/users/batched", query={"user_ids": B_UID})
call("users/batched 多", "GET", "/api/users/batched", query={"user_ids": f"{A_UID},{B_UID}"})

print("\n===== 3. mcp session_token_exchange =====")
call("session_token_exchange", "POST", "/api/mcp/session_token_exchange", {"session_id": "probe"})
call("session_token_exchange2", "POST", "/api/mcp/session_token_exchange", {"code": "probe"})

print("\n===== 4. buzz_approvals =====")
call("buzz create", "POST", "/api/buzz_approvals/create",
     {"file_key": A_DESIGN, "type": "publish"})
call("buzz create2", "POST", "/api/buzz_approvals/create", {"owner_id": A_DESIGN})

print("\n===== 5. subscriptions =====")
call("subscriptions A team", "GET", "/api/subscriptions/", query={"team_id": A_TEAM})
call("subscriptions B team", "GET", "/api/subscriptions/", query={"team_id": B_TEAM})
