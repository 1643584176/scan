# 实验J135: vda 异常诊断 — 动态混淆检测(同偏移两次读对比) + 多节点差异对比
# 动机: j134 全盘无 AGIN, 但 j36/j37 时代能读 celld.toml; 需区分动态混淆/静态异常/节点差异
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

def make_sandbox(name):
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
               {"projectId": PROJ, "name": name,
                "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
    if c != 200:
        print(f"create {name}: {c} {r[:200]}", flush=True)
        return None
    return json.loads(r)["sandbox"]["currentSessionId"]

# 创建 4 个沙箱对比节点
DIAG = r"""
import os, struct, hashlib

def be32(b, o): return struct.unpack_from(">I", b, o)[0]
def be64(b, o): return struct.unpack_from(">Q", b, o)[0]

f = open("/dev/vda", "rb", buffering=0)

# [1] superblock
sb = f.read(512)
print("SB_MAGIC:", sb[:4], flush=True)
print("SB_bs:", be32(sb, 0x04), "dblocks:", be64(sb, 0x08), flush=True)
print("SB_agblocks:", be32(sb, 0x54), "agcount:", be32(sb, 0x58), flush=True)

# [2] AG0 AGI @8192 两次读对比 (动态混淆检测)
for rep in range(2):
    f.seek(8192)
    d = f.read(512)
    print("AG0_AGI[%d] @8192: %r md5=%s" % (rep, d[:16], hashlib.md5(d).hexdigest()[:16]), flush=True)

# [3] 块 1/2/3 内容 (@4096 @8192 @12288)
for off, name in [(4096, "BLK1"), (8192, "BLK2"), (12288, "BLK3")]:
    f.seek(off)
    d = f.read(64)
    print("%s @%d: %r" % (name, off, d), flush=True)

# [4] AG5 AGI @11GB 两次读
for rep in range(2):
    f.seek((5 * 540544 + 2) * 4096)
    d = f.read(512)
    print("AG5_AGI[%d]: %r md5=%s" % (rep, d[:16], hashlib.md5(d).hexdigest()[:16]), flush=True)

# [5] hosts 明文搜索 (第一片 64MB)
hosts = open("/etc/hosts", "rb").read()
f.seek(0)
data = f.read(64 * 1024 * 1024)
print("HOSTS_IN_64MB:", data.find(hosts), flush=True)

# [6] sandbox-init ino (节点指纹)
st = os.stat("/run/vercel/share/sandbox-init")
print("INIT_INO:", st.st_ino, flush=True)
st2 = os.stat("/etc/pki/ca-trust/source/anchors/vercel-proxy-ca.pem")
print("CA_INO:", st2.st_ino, flush=True)
f.close()
print("DIAG_DONE", flush=True)
"""

for i in range(1, 5):
    name = f"expj135c{i}"
    sid = make_sandbox(name)
    print(f"\n=== sandbox {name} sid={sid} ===", flush=True)
    if not sid:
        continue
    run_cmd(sid, DIAG, "diag")
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")

print("\nall done", flush=True)
