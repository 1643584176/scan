# -*- coding: utf-8 -*-
"""vercel_driver2: 第二个账号 (victim) 的 API 驱动
读取 vercel_cookies2.txt (authorization=Bearer xxx)，TEAM2/PROJ2 首次运行时自动发现
"""
import json, os, urllib.request, urllib.error, time


def _load_token():
    tok = os.environ.get("VERCEL_TOKEN2")
    if tok:
        return tok
    p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "vercel_cookies2.txt")
    if not os.path.exists(p):
        raise RuntimeError("vercel_cookies2.txt 不存在: 请放入第二账号 token (authorization=Bearer xxx)")
    c = open(p, encoding="utf-8").read().strip()
    for ln in c.splitlines():
        if ln.startswith("authorization=Bearer "):
            return ln.split("Bearer ")[1].strip()
    raise RuntimeError("vercel_cookies2.txt 格式错误: 需要 authorization=Bearer <token> 行")


TOKEN2 = _load_token()
# 已发现 (2026-08-29): boboli's projects / project-ccwj5
TEAM2 = os.environ.get("VERCEL_TEAM2", "team_jnske5hDpDfj9eDG2PAfDqWf")
PROJ2 = os.environ.get("VERCEL_PROJ2", "prj_LX0QDsEAlWA0uRZvVTunSef3lllF")
BASE = "https://api.vercel.com"


def api(method, path, body=None, timeout=60, team=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Authorization", "Bearer " + TOKEN2)
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]


def discover():
    """发现 victim 账号的 team/project"""
    global TEAM2, PROJ2
    c, r = api("GET", "/v2/user")
    print("user:", c, r[:200])
    c, r = api("GET", "/v2/teams?limit=10")
    print("teams:", c, r[:500])
    if c == 200:
        teams = json.loads(r).get("teams", [])
        if teams:
            TEAM2 = teams[0]["id"]
            print("TEAM2 =", TEAM2, teams[0].get("slug"))
            c, r = api("GET", "/v2/projects?teamId=%s&limit=10" % TEAM2)
            print("projects:", c, r[:300])
            if c == 200:
                projs = json.loads(r)
                if isinstance(projs, dict):
                    projs = projs.get("projects", [])
                if projs:
                    PROJ2 = projs[0]["id"]
                    print("PROJ2 =", PROJ2, projs[0].get("name"))
                else:
                    print("(victim 无 project, 需要先创建)")
            return TEAM2, PROJ2
    print("(victim 无 team)")
    return TEAM2, PROJ2


if __name__ == "__main__":
    discover()
