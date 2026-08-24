# -*- coding: utf-8 -*-
"""实验J287d: 诊断 RECON 代码在沙箱内无输出的原因"""
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
                print("EXIT:", d.get("command", {}), flush=True)
        except Exception:
            print("NONJSON:", line[:400], flush=True)
    return out

NAME = "expj287d"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# 1) 基础环境
out1 = run_cmd(sid, r'''
import sys
print("PY", sys.version, flush=True)
import ctypes
libc = ctypes.CDLL(None, use_errno=True)
r = libc.syscall(39)  # getpid
print("getpid via syscall:", r, "errno:", ctypes.get_errno(), flush=True)
print("OK", flush=True)
''', "BASIC")
print("BASIC OUT:", repr(out1[:500]), flush=True)

# 2) 大代码块 (模拟 RECON 大小)
big = r'''
import ctypes, os, subprocess
libc = ctypes.CDLL(None, use_errno=True)
ENOSYS, EPERM = 38, 1
def sh(cmd, t=6):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, timeout=t)
        return (r.stdout or b"").decode("latin1", "replace")
    except Exception as e:
        return "ERR %s" % e
SYS = %r
def probe(n):
    if n == 101:
        r = libc.syscall(101, 2, -1, 0, 0)
    else:
        r = libc.syscall(n, 0, 0, 0, 0, 0, 0)
    return ctypes.get_errno()
denied, allowed, nosys = [], [], []
for n in sorted(SYS):
    if n in (3, 56, 57, 58, 60, 231, 101):
        continue
    e = probe(n)
    if e == EPERM:
        denied.append(SYS[n])
    elif e == ENOSYS:
        nosys.append(SYS[n])
    else:
        allowed.append((SYS[n], e))
print("DENIED(%d): %s" % (len(denied), ", ".join(denied)), flush=True)
print("ALLOWED(%d): %s" % (len(allowed), ", ".join("%s(%d)" % (n, e) for n, e in allowed)), flush=True)
print("ENOSYS(%d): %s" % (len(nosys), ", ".join(nosys)), flush=True)
print("DONE", flush=True)
'''
SYS_DICT = {
 0:"read",1:"write",2:"open",9:"mmap",10:"mprotect",11:"munmap",12:"brk",
 16:"ioctl",17:"pread64",18:"pwrite64",20:"writev",21:"access",24:"sched_yield",
 25:"mremap",28:"fdatasync",32:"dup",33:"dup2",39:"getpid",40:"sendfile",
 41:"socket",42:"connect",43:"accept",44:"sendto",45:"recvfrom",46:"sendmsg",
 47:"recvmsg",48:"shutdown",49:"bind",50:"listen",51:"getsockname",
 52:"getpeername",53:"socketpair",54:"setsockopt",55:"getsockopt",56:"clone",
 57:"fork",58:"vfork",59:"execve",61:"wait4",62:"kill",63:"uname",
 78:"getdents",79:"getcwd",80:"chdir",81:"fchdir",82:"rename",83:"mkdir",
 85:"creat",86:"link",87:"unlink",88:"symlink",89:"readlink",90:"chmod",
 91:"fchmod",92:"chown",93:"fchown",101:"ptrace",103:"syslog",105:"setuid",
 106:"setgid",107:"seteuid",108:"setegid",110:"getppid",113:"setresuid",
 114:"setresgid",117:"getresuid",118:"getresgid",120:"clone3",121:"setrlimit",
 122:"getrlimit",126:"getsid",127:"sigaltstack",128:"init_module",
 129:"delete_module",130:"get_kernel_syms",131:"quotactl",
 157:"sched_setscheduler",158:"sched_getscheduler",160:"sched_setaffinity",
 161:"sched_getaffinity",165:"mount",166:"umount2",167:"swapon",168:"swapoff",
 169:"reboot",170:"sethostname",171:"setdomainname",172:"iopl",173:"ioperm",
 174:"create_module",180:"pivot_root",181:"chroot",186:"gettid",187:"readahead",
 188:"setxattr",189:"lsetxattr",190:"fsetxattr",191:"getxattr",192:"lgetxattr",
 193:"fgetxattr",194:"listxattr",195:"llistxattr",196:"flistxattr",
 197:"removexattr",198:"lremovexattr",199:"fremovexattr",200:"tkill",
 201:"time",202:"futex",205:"set_thread_area",206:"io_setup",207:"io_destroy",
 208:"io_getevents",209:"io_submit",210:"io_cancel",215:"setgroups",
 220:"getgroups",221:"setfsuid",222:"setfsgid",227:"mlock",228:"munlock",
 229:"mlockall",230:"munlockall",231:"exit_group",233:"epoll_create",
 234:"epoll_ctl",235:"epoll_wait",237:"set_tid_address",238:"timer_create",
 239:"timer_settime",240:"timer_gettime",241:"timer_getoverrun",242:"timer_delete",
 243:"clock_settime",244:"clock_gettime",245:"clock_getres",246:"clock_nanosleep",
 249:"epoll_ctl",250:"tgkill",251:"utimes",252:"statfs",253:"fstatfs",
 255:"gettid",256:"mbind",257:"openat",258:"mkdirat",259:"mknodat",
 260:"fchownat",261:"futimesat",262:"newfstatat",263:"unlinkat",264:"renameat",
 265:"linkat",266:"symlinkat",267:"readlinkat",268:"fchmodat",269:"faccessat",
 270:"pselect6",271:"ppoll",272:"unshare",273:"set_robust_list",
 274:"get_robust_list",275:"splice",276:"tee",277:"sync_file_range",
 278:"vmsplice",279:"move_pages",280:"utimensat",281:"epoll_pwait",
 282:"signalfd",283:"timerfd_create",284:"eventfd",285:"fallocate",
 286:"timerfd_settime",287:"timerfd_gettime",288:"accept4",289:"signalfd4",
 290:"eventfd2",291:"epoll_create1",292:"dup3",293:"pipe2",294:"inotify_init1",
 295:"preadv",296:"pwritev",297:"rt_tgsigqueueinfo",298:"perf_event_open",
 299:"recvmmsg",300:"fanotify_init",301:"fanotify_mark",302:"prlimit64",
 303:"name_to_handle_at",304:"open_by_handle_at",305:"clock_adjtime",
 306:"syncfs",307:"sendmmsg",308:"setns",309:"getcpu",310:"process_vm_readv",
 311:"process_vm_writev",312:"kcmp",313:"finit_module",314:"sched_setattr",
 315:"sched_getattr",316:"renameat2",317:"seccomp",318:"getrandom",
 319:"memfd_create",320:"kexec_file_load",321:"bpf",322:"execveat",
 323:"userfaultfd",324:"membarrier",325:"mlock2",326:"copy_file_range",
 327:"preadv2",328:"pwritev2",329:"pkey_mprotect",330:"pkey_alloc",331:"pkey_free",
 332:"statx",333:"io_pgetevents",334:"rseq",424:"pidfd_send_signal",
 425:"io_uring_setup",426:"io_uring_enter",427:"io_uring_register",
 428:"open_tree",429:"move_mount",430:"fsopen",431:"fsconfig",432:"fsmount",
 433:"fspick",434:"pidfd_open",436:"close_range",437:"openat2",
 438:"pidfd_getfd",439:"faccessat2",440:"process_madvise",441:"epoll_pwait2",
 442:"mount_setattr",443:"quotactl_fd",444:"landlock_create_ruleset",
 445:"landlock_add_rule",446:"landlock_restrict_self",447:"memfd_secret",
 448:"process_mrelease",449:"futex_waitv",
}
code2 = big % repr(SYS_DICT)
out2 = run_cmd(sid, code2, "BIG", timeout=280)
print("BIG OUT len:", len(out2), flush=True)
print(out2[:3000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
