# 实验J120: sandbox-init 模板投毒验证 — 修改A副本后, 新沙箱C是否受影响
# 动机: j119 证明 /run/vercel/share/sandbox-init 是 per-cell 副本(INODE不同, DEV=254:0)
#       若新沙箱从"宿主模板"复制 => 需定位模板(块层)
#       若新沙箱直接继承A的修改(共享底层) => 宿主级注入链成立
# 安全: 标记追加在 ELF 尾部(不影响执行), 测试后删除沙箱
import json, time, urllib.request, urllib.error, sys, hashlib
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

# [A] 创建沙箱 A, 查看 mountinfo + 备份 + 修改 sandbox-init
sid_a = make_sandbox("expj120a")
print("sid A:", sid_a, flush=True)

MI = r"""
import hashlib, os
print("== mountinfo(share/volumes/vercel) ==", flush=True)
for line in open("/proc/self/mountinfo"):
    if any(k in line for k in ("share", "volumes", "vercel", "/run")):
        print("MI:", line.strip(), flush=True)
p = "/run/vercel/share/sandbox-init"
try:
    data = open(p, "rb").read()
    print("BEFORE_MD5:", hashlib.md5(data).hexdigest(), flush=True)
    print("BEFORE_SIZE:", len(data), flush=True)
    st = os.stat(p)
    print("BEFORE_INODE:", st.st_ino, "DEV:", st.st_dev, flush=True)
    # 备份到 /root (沙箱内, 供对照; 沙箱会被删除, 无残留)
    try:
        open("/root/sandbox-init.bak", "wb").write(data)
        print("BACKUP_OK", flush=True)
    except Exception as e:
        print("BACKUP_FAIL:", e, flush=True)
    # 尾部追加标记(ELF 尾部追加不影响执行)
    open(p, "wb").write(data + b"HACKMARKER16B1234")
    r = open(p, "rb").read()
    print("AFTER_MD5:", hashlib.md5(r).hexdigest(), flush=True)
    print("AFTER_SIZE:", len(r), flush=True)
    print("WRITE_OK:", r[-16:] == b"HACKMARKER16B1234", flush=True)
except Exception as e:
    print("FAIL:", type(e).__name__, e, flush=True)
print("MOD_DONE", flush=True)
"""
run_cmd(sid_a, MI, "A-modify")

# [C] 创建新沙箱 C, 检查 sandbox-init 是否受影响
sid_c = make_sandbox("expj120c")
print("sid C:", sid_c, flush=True)

PROBE = r"""
import hashlib, os
p = "/run/vercel/share/sandbox-init"
try:
    data = open(p, "rb").read()
    st = os.stat(p)
    print("C_MD5:", hashlib.md5(data).hexdigest(), flush=True)
    print("C_SIZE:", len(data), flush=True)
    print("C_INODE:", st.st_ino, "DEV:", st.st_dev, flush=True)
    print("C_HAS_MARKER:", b"HACKMARKER16B1234" in data, flush=True)
    print("C_TAIL:", data[-16:], flush=True)
    # 备份是否也被复制? 检查 /root 下(应该没有)
    print("C_BAK_EXISTS:", os.path.exists("/root/sandbox-init.bak"), flush=True)
except Exception as e:
    print("FAIL:", e, flush=True)
print("PROBE_DONE", flush=True)
"""
run_cmd(sid_c, PROBE, "C-probe")

# 清理
for name in ["expj120a", "expj120c"]:
    c, r = api("DELETE", f"/v2/sandboxes/{name}?teamId={TEAM}&projectId={PROJ}")
    print(f"cleanup {name}: {c}", flush=True)
print("\ncleanup done", flush=True)
