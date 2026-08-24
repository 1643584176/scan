# 实验G4b驱动: 两种 forwardURL 目标(httpbin vs postman-echo)对比
import json, base64, pathlib, urllib.request, urllib.error

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
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

NAME = "expg4b"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom",
                              "allowedDomains": ["httpbin.org", "api.vercel.com", "postman-echo.com"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

payload = base64.b64encode(pathlib.Path("exp_g4b.py").read_bytes()).decode()
run_body = {"command": "python3", "args": ["-c", f"import base64;exec(base64.b64decode('{payload}').decode())"],
            "wait": True, "logs": True, "timeout": 60000}

def show(r, label):
    print(f"--- {label} ---")
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

# 轮次1: forwardURL=httpbin.org/anything
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
           {"allow": {"api.vercel.com": [
               {"match": {"path": {"startsWith": "/v2"}},
                "forwardURL": "https://httpbin.org/anything"}]}})
print("update(httpbin):", c, r[:120])
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", run_body)
show(r, "ROUND1 httpbin")

# 轮次2: forwardURL=postman-echo.com/headers
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/network-policy?teamId={TEAM}",
           {"allow": {"api.vercel.com": [
               {"match": {"path": {"startsWith": "/v2"}},
                "forwardURL": "https://postman-echo.com/headers"}]}})
print("update(postman):", c, r[:120])
c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", run_body)
show(r, "ROUND2 postman-echo")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done")
