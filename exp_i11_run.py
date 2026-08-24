# I10 运行流程: 创建沙箱 -> 执行 exp_i16.py -> 输出 -> 删除
import json, base64, pathlib, urllib.request, urllib.error, time

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=90):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:800]

NAME = "expi16"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME, "networkPolicy": {"mode": "deny-all"}})
print("create:", c, flush=True)
sid = json.loads(r).get("sandbox", {}).get("currentSessionId", "")
print("sid:", sid, flush=True)

payload = base64.b64encode(pathlib.Path("exp_i16.py").read_bytes()).decode()
body = {"command": "python3", "args": ["-u", "-c", f"import base64;exec(base64.b64decode('{payload}').decode())"],
        "wait": True, "logs": True, "timeout": 180000}
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body, timeout=240)
print("cmd:", c, flush=True)
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
        pass

time.sleep(2)
c, r = api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ndelete:", c)
