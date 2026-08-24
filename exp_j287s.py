# -*- coding: utf-8 -*-
"""实验J287s: 找23456/30001/30002监听者(root进程) + dump其内存挖路由"""
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

NAME = "expj287s"
api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
c, r = api("POST", f"/v2/sandboxes?teamId={TEAM}",
           {"projectId": PROJ, "name": NAME})
if c != 200:
    print("create fail", r[:300], flush=True)
    sys.exit(1)
sid = json.loads(r)["sandbox"]["currentSessionId"]
print("sid:", sid, flush=True)

# cmd1: 找 TCP 监听者 (inode 匹配)
out = run_cmd(sid, r'''
import os, re
# tcp6 监听 inode
tcp6 = open("/proc/net/tcp6").read()
listen_inodes = {}
for line in tcp6.splitlines()[1:]:
    parts = line.split()
    st = parts[3]
    if st == "0A":  # LISTEN
        listen_inodes[int(parts[9])] = parts[1]
print("LISTEN inodes:", listen_inodes, flush=True)
# 遍历所有进程 fd
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    try:
        status = open("/proc/%s/status" % pid).read()
        uid_line = [l for l in status.splitlines() if l.startswith("Uid:")][0]
        uid = uid_line.split()[1]
        cmd = open("/proc/%s/cmdline" % pid).read().replace("\x00", " ").strip()
        if not cmd:
            cmd = "[" + open("/proc/%s/comm" % pid).read().strip() + "]"
    except Exception:
        continue
    sockfds = []
    try:
        for fd in os.listdir("/proc/%s/fd" % pid):
            try:
                t = os.readlink("/proc/%s/fd/%s" % (pid, fd))
            except Exception:
                continue
            m = re.search(r"socket:\[(\d+)\]", t)
            if m and int(m.group(1)) in listen_inodes:
                sockfds.append("%s->%s" % (fd, t))
    except Exception:
        pass
    if sockfds:
        print("PID %s uid=%s cmd=%r FDS: %s" % (pid, uid, cmd, "; ".join(sockfds)), flush=True)
print("DONE", flush=True)
''', "FIND_LSN", timeout=100)
print("FIND_LSN out:", repr((out or "")[:3000]), flush=True)

# cmd2: dump 监听者内存挖路径 (从 cmd1 结果取 pid, 这里假设是第一个 root 进程)
out = run_cmd(sid, r'''
import os, re
# 找所有 root 进程里 fd 指向 listen inode 的
tcp6 = open("/proc/net/tcp6").read()
listen_inodes = set()
for line in tcp6.splitlines()[1:]:
    parts = line.split()
    if parts[3] == "0A":
        listen_inodes.add(int(parts[9]))
cands = []
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    try:
        for fd in os.listdir("/proc/%s/fd" % pid):
            try:
                t = os.readlink("/proc/%s/fd/%s" % (pid, fd))
            except Exception:
                continue
            m = re.search(r"socket:\[(\d+)\]", t)
            if m and int(m.group(1)) in listen_inodes:
                cands.append(pid)
    except Exception:
        pass
cands = sorted(set(cands))
print("CAND PIDS:", cands, flush=True)
for pid in cands:
    try:
        cmd = open("/proc/%s/cmdline" % pid).read().replace("\x00", " ").strip()
        exe = os.readlink("/proc/%s/exe" % pid)
        print("PID %s exe=%s cmd=%r" % (pid, exe, cmd), flush=True)
    except Exception as e:
        print("PID %s info EXC %s" % (pid, e), flush=True)

# dump 第一个候选的内存 (maps + 字符串)
if cands:
    pid = cands[0]
    maps = open("/proc/%s/maps" % pid).read()
    segs = []
    for line in maps.splitlines():
        p = line.split()
        if len(p) < 6:
            continue
        lo, hi = [int(x, 16) for x in p[0].split("-")]
        if "r" in p[1] and (p[5].startswith("/") or p[5] == "0"):
            segs.append((lo, hi, p[5]))
    print("SEGS %d for pid %s" % (len(segs), pid), flush=True)
    try:
        fd = os.open("/proc/%s/mem" % pid, os.O_RDONLY)
    except Exception as e:
        print("MEM OPEN EXC:", e, flush=True)
        fd = None
    if fd:
        hits = set()
        for lo, hi, path in segs:
            size = min(hi - lo, 4 * 1024 * 1024)
            try:
                os.lseek(fd, lo, 0)
                data = os.read(fd, size)
            except Exception:
                continue
            for m in re.finditer(rb'/[a-zA-Z0-9_./-]{2,60}', data):
                s = m.group(0).decode("latin1", "replace")
                if any(k in s for k in ("api", "v1", "v2", "health", "metric", "log", "exec", "cmd", "file", "fs", "run", "spawn", "sandbox", "internal", "debug", "status", "event", "socket")):
                    hits.add(s)
            for m in re.finditer(rb'[A-Za-z]+\.[A-Za-z]+\.[vV][0-9]+\.[A-Za-z]+Service/[A-Za-z]+', data):
                hits.add(m.group(0).decode("latin1", "replace"))
        os.close(fd)
        print("HITS %d:" % len(hits), flush=True)
        for h in sorted(hits):
            print(h, flush=True)
''', "DUMP_LSN", timeout=280)
print("DUMP_LSN out len:", len(out or ""), flush=True)
print((out or "")[:15000], flush=True)

api("DELETE", f"/v2/sandboxes/{NAME}?teamId={TEAM}&projectId={PROJ}")
print("\ncleanup done", flush=True)
