# 实验J119: sandbox-init 共享性验证 — 双沙箱对比(决定宿主 RCE 链可行性)
# 动机: 若所有沙箱的 /run/vercel/share/sandbox-init 是同一宿主文件(bind mount 自 vda)
#       => 写 vda 该文件 = 跨沙箱持久化代码注入(宿主级), 报告 3 候选
#       若 per-sandbox 独立 => 宿主 RCE 链不可行, 放弃
import json, time, urllib.request, urllib.error, sys, hashlib
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

def run_cmd(sid, code, label, wait=True, timeout=300):
    body = {"command": "python3", "args": ["-c", code],
            "wait": wait, "logs": True, "timeout": timeout}
    for attempt in range(6):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        time.sleep(4)
    print(f"=== cmd[{label}] status {c} ===", flush=True)
    if c != 200:
        print(f"  RAW: {r[:400]}", flush=True)
        return ""
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
    return ""

def make_sandbox(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    if c != 200:
        print(f"create {name}: {c} {r[:200]}", flush=True)
        return None
    return json.loads(r)["sandbox"]["currentSessionId"]

PROBE = r"""
import hashlib, os

p = "/run/vercel/share/sandbox-init"
try:
    data = open(p, "rb").read()
    st = os.stat(p)
    print("MD5:", hashlib.md5(data).hexdigest(), flush=True)
    print("SIZE:", len(data), flush=True)
    print("INODE:", st.st_ino, flush=True)
    print("DEV:", st.st_dev, flush=True)
    print("MODE:", oct(st.st_mode), flush=True)
    print("HEAD:", data[:64].hex(), flush=True)
    print("TAIL:", data[-64:].hex(), flush=True)
    # ELF 关键偏移(与宿主文件对比用)
    print("ELF_OFFSETS:", flush=True)
    for sig in [b"Go build ID", b"go1.2", b"golang"]:
        i = data.find(sig)
        print("  %s @ %d" % (sig, i), flush=True)
except Exception as e:
    print("FAIL:", e, flush=True)
print("PROBE_DONE", flush=True)
"""

sid_a = make_sandbox("expj119a")
print("sid A:", sid_a, flush=True)
run_cmd(sid_a, PROBE, "A-init-stat")

sid_b = make_sandbox("expj119b")
print("sid B:", sid_b, flush=True)
run_cmd(sid_b, PROBE, "B-init-stat")

for name in ["expj119a", "expj119b"]:
    c, r = api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    print(f"cleanup {name}: {c}", flush=True)
print("\ncleanup done", flush=True)
