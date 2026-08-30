# -*- coding: utf-8 -*-
"""celld_probe 驱动: 创建 deny-all 沙箱 -> 注入 guest 脚本 -> 执行 -> 拉取结果
token 加载优先级: 环境变量 VERCEL_TOKEN > vercel_cookies.txt"""
import base64, json, os, sys, time, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))


def load_token():
    tok = os.environ.get("VERCEL_TOKEN")
    if tok:
        return tok
    p = os.path.join(os.path.dirname(HERE), "vercel_cookies.txt")
    c = open(p, encoding="utf-8").read().strip()
    for ln in c.splitlines():
        if ln.startswith("authorization=Bearer "):
            return ln.split("Bearer ")[1].strip()
    raise RuntimeError("no token")


TOKEN = load_token()
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


def fresh_sandbox(name):
    api("DELETE", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
    time.sleep(2)
    body = {"projectId": PROJ, "name": name,
            "networkPolicy": {"mode": "deny-all"}}
    c, r = api("POST", "/v2/sandboxes?teamId=%s" % TEAM, body)
    print("create:", c, r[:400], flush=True)
    if c != 200:
        raise RuntimeError("create failed: %s" % r[:300])
    d = json.loads(r)
    return d["sandbox"]["currentSessionId"]


def cmd(sid, command, args, timeout_ms=60000):
    body = {"command": command, "args": args, "wait": True, "logs": True,
            "timeout": timeout_ms}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/cmd?teamId=%s" % (sid, TEAM), body,
               timeout=timeout_ms / 1000 + 30)
    return c, r


def run():
    sid = fresh_sandbox("celld1")
    print("sid:", sid, flush=True)
    time.sleep(2)
    code = open(os.path.join(HERE, "celld_probe_guest.py"), "rb").read()
    payload = base64.b64encode(code).decode()
    inject = "import base64;open('/vercel/sandbox/celld_probe.py','wb').write(base64.b64decode('%s'))" % payload
    c, r = cmd(sid, "python3", ["-c", inject], timeout_ms=30000)
    print("inject:", c, r[:200], flush=True)
    c, r = cmd(sid, "python3", ["/vercel/sandbox/celld_probe.py"], timeout_ms=120000)
    print("run:", c, flush=True)
    if c == 200:
        print(r[:800], flush=True)
    for attempt in range(5):
        time.sleep(2)
        c, r = cmd(sid, "cat", ["/vercel/sandbox/celld_probe.out"], timeout_ms=30000)
        if c == 200 and "CELD_DONE" in r:
            print("=== 结果 ===", flush=True)
            print(r, flush=True)
            return sid, r
        print("attempt %d status=%d" % (attempt, c), flush=True)
    c, r = cmd(sid, "cat", ["/vercel/sandbox/celld_probe.out"], timeout_ms=30000)
    print("=== 最后结果 ===", flush=True)
    print(r, flush=True)
    return sid, r


if __name__ == "__main__":
    run()
