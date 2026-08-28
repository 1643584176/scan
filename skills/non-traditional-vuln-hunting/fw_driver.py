# -*- coding: utf-8 -*-
"""Firewall bypass 测试驱动: 创建 deny-all 沙箱并执行 guest 内测试"""
import json, os, urllib.request, urllib.error, time, sys

# Read Vercel PAT from env instead of hardcoding (push protection blocks commits with secrets)
TOKEN = os.environ["VERCEL_TOKEN"]
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"
BASE = "https://api.vercel.com"


def api(method, path, body=None, timeout=90):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:800]


def fresh_sandbox_deny_all(name):
    """删除同名旧沙箱, 创建 deny-all 策略沙箱"""
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": name,
            "networkPolicy": {"mode": "deny-all"}}
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
    print("create:", c, r[:400])
    if c != 200:
        raise RuntimeError("create failed")
    d = json.loads(r)
    sid = d["sandbox"]["currentSessionId"]
    print("sessionId:", sid)
    return sid


def cmd(sid, command, args, timeout_ms=60000):
    body = {"command": command, "args": args, "wait": True, "logs": True,
            "timeout": timeout_ms}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM), body,
               timeout=timeout_ms / 1000 + 30)
    return c, r


if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest1")
    print(sid)
