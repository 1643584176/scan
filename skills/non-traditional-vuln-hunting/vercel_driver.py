# -*- coding: utf-8 -*-
"""Vercel Sandbox API 驱动(从历史会话恢复, 2026-08-28 重建)"""
import json, os, urllib.request, urllib.error, time

# Read Vercel PAT from env instead of hardcoding (push protection blocks commits with secrets)
TOKEN = os.environ["VERCEL_TOKEN"]
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"
BASE = "https://api.vercel.com"


def api(method, path, body=None, timeout=60):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]


def list_sandboxes():
    """列表用 ?project=(非 projectId)"""
    c, r = api("GET", "/v2/sandboxes?teamId=%s&project=%s&limit=50" % (TEAM, PROJ))
    return c, r


def fresh_sandbox(name, network_mode="allow-all"):
    """删除同名旧沙箱后重建, 返回 currentSessionId"""
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": name}
    if network_mode == "custom":
        body["networkPolicy"] = {"mode": "custom", "allowedDomains": ["httpbin.org"]}
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
    print("create:", c, r[:300])
    if c != 200:
        raise RuntimeError("create sandbox failed: %d %s" % (c, r[:300]))
    d = json.loads(r)
    return d["sandbox"]["currentSessionId"]


def cmd(sid, command, args, timeout_ms=60000):
    """执行命令, 返回 stdout 文本"""
    body = {"command": command, "args": args, "wait": True, "logs": True,
            "timeout": timeout_ms}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM), body,
               timeout=timeout_ms / 1000 + 30)
    return c, r


if __name__ == "__main__":
    c, r = list_sandboxes()
    print("list sandboxes:", c)
    print(r[:1500])
