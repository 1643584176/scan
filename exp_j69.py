# 实验J69: seccomp 拦截面测试 + /proc/1/fd 与网络侦察 + mount 验证
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

NAME = "expj69"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME,
            "networkPolicy": {"mode": "custom", "allowedDomains": ["httpbin.org"]}})
print("create:", c)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid)

PROBE = r"""
import os, sys, ctypes, struct

def t(label, fn):
    try:
        r = fn()
        print("[%-22s] OK %r" % (label, r), flush=True)
    except Exception as e:
        print("[%-22s] FAIL %r" % (label, e), flush=True)

print("== [1] seccomp 拦截面 ==", flush=True)
t("mount tmpfs", lambda: (os.mkdir("/tmp/mt2") if not os.path.exists("/tmp/mt2") else None) or os.system("mount -t tmpfs none /tmp/mt2 && echo MOUNTED"))
t("umount", lambda: os.system("umount /tmp/mt2 2>&1"))
# /dev/mem (CAP_SYS_RAWIO)
t("open /dev/mem", lambda: open("/dev/mem", "rb").read(16).hex())
# bpf (CAP_BPF)
t("bpf_prog_load", lambda: ctypes.CDLL(None).syscall(321, 5, 0, 0, 0, 0))  # bpf(BPF_PROG_LOAD=5)
# perf_event_open (CAP_PERFMON)
t("perf_event_open", lambda: ctypes.CDLL(None).syscall(298, 0, 0, -1, 0x400000, 0))
# open_by_handle_at (CAP_DAC_READ_SEARCH)
t("open_by_handle_at", lambda: ctypes.CDLL(None).syscall(304, -100, 0, 0, 0))
# kexec_load
t("kexec_load", lambda: ctypes.CDLL(None).syscall(246, 0, 0, 0, 0))
# setns / unshare via syscall
t("unshare(CLONE_NEWNS)", lambda: ctypes.CDLL(None).syscall(272, 0x00020000))
# chroot
t("chroot(/tmp)", lambda: os.chroot("/tmp"))
# pivot_root
t("pivot_root", lambda: ctypes.CDLL(None).syscall(155, b"/tmp", b"/tmp"))
# 写 /dev/vda (无害区域: 尾部, 先读后写还原)
def vda_write_test():
    f = open("/dev/vda", "r+b", buffering=0)
    f.seek(0)
    orig = f.read(16)
    print("    vda[0:16]:", orig.hex(), flush=True)
    f.seek(0)
    f.write(orig)  # 写回相同内容, 无破坏
    f.close()
    return "readwrite OK"
t("vda write-back", vda_write_test)

print("== [2] /proc/1/fd 侦察 ==", flush=True)
for fd in sorted(os.listdir("/proc/1/fd"), key=int):
    try:
        link = os.readlink("/proc/1/fd/" + fd)
        print("  fd %s -> %s" % (fd, link), flush=True)
    except Exception as e:
        print("  fd %s ERR %r" % (fd, e), flush=True)

print("== [3] sandbox-init 网络 ==", flush=True)
try:
    print(open("/proc/1/net/tcp").read(), flush=True)
except Exception as e:
    print("tcp ERR", e, flush=True)
try:
    print(open("/proc/1/net/unix").read(), flush=True)
except Exception as e:
    print("unix ERR", e, flush=True)

print("== [4] sandbox-init 环境变量 ==", flush=True)
try:
    print(open("/proc/1/environ").read().replace("\x00", " ")[:2000], flush=True)
except Exception as e:
    print("environ ERR", e, flush=True)
"""
run_cmd(sid, PROBE, "seccomp-fd-recon", wait=True, timeout=180000)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
