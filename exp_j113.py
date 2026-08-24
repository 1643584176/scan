# 实验J113: sandbox-init 二进制静态分析 — 找 cell 级凭据/隐藏配置路径/签名密钥
# 动机: /run/vercel/share/sandbox-init (16MB Go 二进制) 沙箱内可读, 之前只查 environ/cmdline,
#       未做字符串层挖掘; 若含 cell 凭据/私钥 => 直接凭据窃取报告
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

NAME = "expj113"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c, flush=True)
if c != 200:
    print(r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

PROBE = r"""
import re, os

BIN = "/run/vercel/share/sandbox-init"
data = open(BIN, "rb").read()
print("BIN size:", len(data), flush=True)
print("ELF magic:", data[:4], flush=True)
print("Go buildinfo:", b"Go build ID" in data[:64*1024] or b"Go build ID" in data, flush=True)

patterns = [
    (b"BEGIN", "PEM-BEGIN", 90),
    (b"PRIVATE KEY", "PRIVATE-KEY", 120),
    (b"ED25519", "ED25519", 80),
    (b"ed25519", "ed25519", 80),
    (b"x-signature", "x-signature", 80),
    (b"X-Signature", "X-Signature", 80),
    (b"pubkey", "pubkey", 100),
    (b"pub_key", "pub_key", 100),
    (b"secret", "secret", 100),
    (b"api_key", "api_key", 80),
    (b"apikey", "apikey", 80),
    (b"Bearer ", "Bearer", 90),
    (b"token", "token", 90),
    (b"oidc", "oidc", 90),
    (b"/run/cell", "/run/cell", 120),
    (b"/volumes", "/volumes", 120),
    (b"/opt/vercel", "/opt/vercel", 120),
    (b"/run/vercel", "/run/vercel", 120),
    (b"ca-cert", "ca-cert", 90),
    (b"ca-key", "ca-key", 90),
    (b"http://", "http://", 100),
    (b"https://", "https://", 100),
    (b"wss://", "wss://", 100),
    (b"169.254", "IMDS", 80),
    (b"100.64", "CGNAT", 80),
    (b"metadata", "metadata", 80),
    (b"credential", "credential", 100),
    (b"authn", "authn", 100),
    (b"authz", "authz", 100),
]

def ctx(data, pos, n):
    s = max(0, pos - 20)
    e = min(len(data), pos + n)
    seg = data[s:e]
    # 只保留可打印
    out = []
    for b in seg:
        if 32 <= b < 127:
            out.append(chr(b))
        else:
            out.append(".")
    return "".join(out)

for pat, label, width in patterns:
    hits = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        hits.append(ctx(data, i, width))
        start = i + 1
        if len(hits) >= 6:
            break
    if hits:
        print(f"[{label}] {len(hits)}+ hits:", flush=True)
        for h in hits:
            print("   ", h, flush=True)
    else:
        print(f"[{label}] 0", flush=True)

# URL 提取 (全局)
urls = set(re.findall(rb"https?://[A-Za-z0-9._\-/:]+", data))
print(f"\nURLs ({len(urls)}):", flush=True)
for u in sorted(urls)[:40]:
    print("   ", u.decode(errors="replace")[:120], flush=True)

# 32/64 字符 hex/base64 疑似 token
tok = set()
for m in re.finditer(rb"[A-Za-z0-9+/_\-]{32,64}={0,2}", data):
    s = m.group()
    if len(set(s)) > 8 and not s.isdigit():
        tok.add(s.decode())
print(f"\nCandidate tokens ({len(tok)}):", flush=True)
for t in sorted(tok)[:30]:
    print("   ", t, flush=True)
print("ANALYZE_DONE", flush=True)
"""

run_cmd(sid, PROBE, "bin-analysis", wait=True, timeout=300000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
