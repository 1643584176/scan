# -*- coding: utf-8 -*-
"""vda26_curl_h2: curl --http2-prior-knowledge gRPC Exec 流式测试
P1: attach 保活验证 (Start 后 Wait 3s 判断进程存活)
P2: curl h2 gRPC Exec (f9=cid, f1=id) 流式响应
P3: curl h2 connect+proto Exec
P4: curl h2 Process StreamOutput
输出落盘 + 哨兵 V26M_DONE"""
import os, time, socket, ctypes, re, struct, subprocess

OUT = '/vercel/sandbox/v26m.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rpc_raw(sockpath, path, body, ctype, t=6, shutdown_wr=False, te=None):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        if isinstance(body, str):
            body = body.encode()
        hdr = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Content-Length: %d\r\nConnection: close\r\n' % (path, ctype, len(body)))
        if te:
            hdr += 'TE: %s\r\n' % te
        hdr += '\r\n'
        s.sendall(hdr.encode() + body)
        if shutdown_wr:
            try:
                s.shutdown(socket.SHUT_WR)
            except Exception:
                pass
        data = b''
        while True:
            try:
                chunk = s.recv(16384)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:1500].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def grpc_env(payload):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def pstr(field_no, s):
    b = s.encode()
    tag = (field_no << 3) | 2
    out = bytearray()
    while tag > 127:
        out.append((tag & 127) | 128)
        tag >>= 7
    out.append(tag)
    l = len(b)
    while l > 127:
        out.append((l & 127) | 128)
        l >>= 7
    out.append(l)
    return bytes(out) + b


def pbool(field_no, v):
    tag = (field_no << 3) | 0
    out = bytearray()
    while tag > 127:
        out.append((tag & 127) | 128)
        tag >>= 7
    out.append(tag)
    out.append(1 if v else 0)
    return bytes(out)


def curl_h2(sockpath, path, body, ctype, t=10, extra=None):
    """curl --http2-prior-knowledge --unix-socket POST"""
    try:
        tmp = '/tmp/curl_req_%d.bin' % os.getpid()
        open(tmp, 'wb').write(body)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', sockpath, '-X', 'POST',
               '-H', 'Content-Type: %s' % ctype,
               '-H', 'TE: trailers',
               '--data-binary', '@%s' % tmp,
               'http://unix%s' % path]
        if extra:
            cmd += extra
        r = subprocess.run(cmd, capture_output=True, timeout=t + 3)
        out = r.stdout.decode('utf-8', errors='replace')
        err = r.stderr.decode('utf-8', errors='replace')[:200]
        return 'rc=%d' % r.returncode, (out + ' | STDERR: ' + err)[:800].replace('\n', ' ')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def main():
    MOUNTED = False
    try:
        for ln in open('/proc/self/mountinfo', errors='replace'):
            if '/mnt/vdax' in ln:
                MOUNTED = True
                break
    except Exception:
        pass
    if not MOUNTED:
        os.makedirs('/mnt/vdax', exist_ok=True)
        ret = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax', b'xfs', 0, b'')
        log('mount ret=%d' % ret)

    sp = '/mnt/vdax/run/cell/cell.sock'
    IMG = '977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59'
    CSVC = '/vercel.hive.cell.api.containers.v1.ContainersService'
    PSVC = '/vercel.hive.cell.api.processes.v1.ProcessService'

    # P1: attach 保活验证
    log('=== P1 attach keepalive ===')
    st, bd = rpc_raw(sp, CSVC + '/Create', '{"image":"%s","command":"/bin/sleep 300","attach":true}' % IMG,
                     'application/json', t=30)
    m = re.search(r'"containerId":\s*"([^"]+)"', bd)
    if not m:
        log('NO CID - abort')
        log('V26M_DONE')
        f.close()
        return
    cid = m.group(1)
    log('CID=%s' % cid)
    st, bd = rpc_raw(sp, CSVC + '/Start', '{"container_id":"%s"}' % cid, 'application/json', t=6)
    log('start -> %s | %s' % (st, bd[:150]))
    st, bd = rpc_raw(sp, CSVC + '/Wait', '{"container_id":"%s"}' % cid, 'application/json', t=3)
    log('wait3s -> %s | %s  [%s]' % (st, bd[:150], 'RUNNING' if st == 'NORESP' else 'EXITED'))

    # P2: curl h2 gRPC Exec
    log('=== P2 curl h2 gRPC Exec ===')
    payloads = [
        ('f9,f1 id', pstr(9, cid) + pstr(1, 'id')),
        ('f9,f1 shell', pstr(9, cid) + pstr(1, '/bin/sh -c id;uname -a;echo MARK-26')),
        ('f9 only', pstr(9, cid)),
    ]
    for tag, payload in payloads:
        st, bd = curl_h2(sp, CSVC + '/Exec', grpc_env(payload), 'application/grpc', t=10)
        log('curl exec %-12s -> %s | %s' % (tag, st, bd[:500]))
        time.sleep(0.3)

    # P3: curl h2 connect+proto Exec
    log('=== P3 curl h2 connect Exec ===')
    st, bd = curl_h2(sp, CSVC + '/Exec', b'\x00' + struct.pack('>I', len(pstr(9, cid) + pstr(1, 'id'))) + pstr(9, cid) + pstr(1, 'id'),
                     'application/connect+proto', t=8)
    log('curl connect exec -> %s | %s' % (st, bd[:400]))

    # P4: curl h2 Process StreamOutput (connect+proto 对比)
    log('=== P4 curl h2 Proc Stream ===')
    pid27 = 'hvcp_' + 'a' * 27
    payload = pstr(1, pid27) + pbool(2, True)
    st, bd = curl_h2(sp, PSVC + '/StreamOutput', b'\x00' + struct.pack('>I', len(payload)) + payload,
                     'application/connect+proto', t=8)
    log('curl proc stream -> %s | %s' % (st, bd[:400]))
    st, bd = curl_h2(sp, PSVC + '/StreamOutput', grpc_env(payload), 'application/grpc', t=8)
    log('curl proc grpc -> %s | %s' % (st, bd[:400]))

    # P5: Kill
    st, bd = rpc_raw(sp, CSVC + '/Kill', '{"container_id":"%s"}' % cid, 'application/json', t=4)
    log('kill -> %s | %s' % (st, bd[:150]))

    log('V26M_DONE')
    f.close()


if __name__ == '__main__':
    main()
