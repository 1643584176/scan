# 实验J134: vda 内容级定位 — hosts/CA证书明文匹配 + AGIN 分布扫描
# 动机: AG5 AGI magic=AB3C(异常), 元数据疑似混淆; 用文件内容特征绕过元数据定位
# 纯读操作, 零破坏
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

def run_cmd(sid, code, label, wait=True, timeout=600, args=None):
    body = {"command": "python3", "args": (args or ["-c", code]),
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

NAME = "expj134"
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

SCAN = r"""
import sys, time, hashlib

# 特征收集 (沙箱内读取)
hosts = open("/etc/hosts", "rb").read()
print("HOSTS(%d): %r" % (len(hosts), hosts), flush=True)
ca = None
for p in ["/etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem",
          "/usr/local/share/ca-certificates/vercel-proxy-ca.crt"]:
    try:
        ca = open(p, "rb").read()
        break
    except Exception:
        pass
print("CA(%d): %r" % (len(ca), ca), flush=True)
ca_head = ca[:64] if ca else None
hosts_head = hosts[:64]

start = int(sys.argv[1]); end = int(sys.argv[2])
BS = 8 * 1024 * 1024
f = open("/dev/vda", "rb", buffering=0)
f.seek(start)
pos = start
t0 = time.time()
hits = []
try:
    while pos < end:
        chunk = f.read(BS)
        if not chunk:
            break
        pos += len(chunk)
        # AGIN magic 分布 (每 AG 一个, 位置 = (agno*540544+2)*4096)
        i = chunk.find(b"AGIN")
        if i >= 0:
            off = pos - len(chunk) + i
            print("AGIN @%d (agno~%d)" % (off, off // (540544 * 4096)), flush=True)
        # hosts 明文
        i = chunk.find(hosts)
        if i >= 0:
            off = pos - len(chunk) + i
            print("HOSTS_PLAIN @%d" % off, flush=True)
            hits.append(("HOSTS", off))
        # CA 明文 (完整)
        if ca:
            i = chunk.find(ca)
            if i >= 0:
                off = pos - len(chunk) + i
                print("CA_PLAIN @%d" % off, flush=True)
                hits.append(("CA", off))
        # CA 头 (可能被部分覆盖)
        if ca_head:
            i = chunk.find(ca_head)
            if i >= 0:
                off = pos - len(chunk) + i
                print("CA_HEAD @%d" % off, flush=True)
                hits.append(("CA_HEAD", off))
        # hosts 头
        i = chunk.find(hosts_head)
        if i >= 0:
            off = pos - len(chunk) + i
            print("HOSTS_HEAD @%d" % off, flush=True)
            hits.append(("HOSTS_HEAD", off))
        now = time.time()
        if now - t0 >= 20:
            print("PROGRESS %.2f GB %.0fs" % (pos / 2**30, now - t0), flush=True)
            t0 = now
finally:
    f.close()
print("SCAN_DONE %d hits" % len(hits), flush=True)
print("HITS: %r" % hits, flush=True)
"""

# 33GB 分 7 片
slices = [(i * 5 * 2**30, (i + 1) * 5 * 2**30) for i in range(7)]
for idx, (s, e) in enumerate(slices):
    print(f"\n--- vda slice {idx}: {s} - {e} ---", flush=True)
    run_cmd(sid, SCAN, f"scan-slice{idx}", args=["-c", SCAN, str(s), str(e)])

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
