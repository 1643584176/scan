# -*- coding: utf-8 -*-
"""实验J287o: 枚举283-449完成seccomp面 + 127.0.0.1 loopback扫描 + UDP8125"""
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

NAME = "expj287o"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# cmd1: 枚举 283-449 (跳过 271/282 kill 点), 慢节奏+逐个print
out = run_cmd(sid, r'''
import ctypes, time
libc = ctypes.CDLL(None, use_errno=True)
NS = {283:"timerfd_create",284:"eventfd",285:"fallocate",286:"timerfd_settime",
287:"timerfd_gettime",288:"accept4",289:"signalfd4",290:"eventfd2",
291:"epoll_create1",292:"dup3",293:"pipe2",294:"inotify_init1",295:"preadv",
296:"pwritev",297:"rt_tgsigqueueinfo",298:"perf_event_open",299:"recvmmsg",
300:"fanotify_init",301:"fanotify_mark",302:"prlimit64",303:"name_to_handle_at",
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
448:"process_mrelease",449:"futex_waitv"}
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
''', "ENUM283", timeout=280)
print("ENUM283 out len:", len(out or ""), flush=True)
print((out or "")[:9000], flush=True)

# cmd2: 127.0.0.1 TCP 全端口并发扫描
out = run_cmd(sid, r'''
import socket, threading, time
open_ports = []
lock = threading.Lock()
def try_conn(p):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.35)
        s.connect(("127.0.0.1", p))
        with lock:
            open_ports.append(p)
    except Exception:
        pass
    finally:
        try: s.close()
        except Exception: pass
def worker(ports):
    for p in ports:
        try_conn(p)
chunks = []
allp = list(range(1, 65536))
step = 65536 // 300
for i in range(0, 65536, step):
    chunks.append(allp[i:i+step])
threads = [threading.Thread(target=worker, args=(c,)) for c in chunks]
t0 = time.time()
for t in threads: t.start()
for t in threads: t.join()
open_ports.sort()
print("LOOPBACK TCP OPEN:", open_ports, flush=True)
print("scan took %.1fs" % (time.time()-t0), flush=True)
''', "SCAN_LO", timeout=280)
print("SCAN_LO out:", repr((out or "")[:1500]), flush=True)

# cmd3: UDP 探测 127.0.0.1 常见端口 + 8125
out = run_cmd(sid, r'''
import socket, time
def udp_probe(port, payload=b"ping", timeout=2):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.sendto(payload, ("127.0.0.1", port))
        try:
            d, _ = s.recvfrom(4096)
            return "RECV %dB: %r" % (len(d), d[:80])
        except socket.timeout:
            return "NO_RESP"
        except Exception as e:
            return "ERR %s" % type(e).__name__
    except Exception as e:
        return "SEND_ERR %s" % type(e).__name__
    finally:
        s.close()
for p in [53, 67, 68, 123, 161, 500, 1900, 5353, 8125, 8126, 9100, 2003, 3000, 8000, 8080]:
    print("UDP 127.0.0.1:%d %s" % (p, udp_probe(p)), flush=True)
# 再发一次 8125 大包
print("UDP 8125 big:", udp_probe(8125, b"{\"metric\":\"x\",\"value\":1}\n"*5), flush=True)
''', "UDP_LO", timeout=100)
print("UDP_LO out:", repr((out or "")[:1200]), flush=True)

# cmd4: 重读 conntrack 观察变化
out = run_cmd(sid, r'''
import subprocess
def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace")
    except Exception as e:
        return "ERR %s" % e
print(sh("cat /proc/net/nf_conntrack"), flush=True)
''', "CT2", timeout=100)
print("CT2 out:", repr((out or "")[:1500]), flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
