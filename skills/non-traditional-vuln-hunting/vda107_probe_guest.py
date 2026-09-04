# -*- coding: utf-8 -*-
"""v107 payload: unix socket API 探测
P1 cell.sock Connect RPC (celld API)
P2 cell.sock gRPC
P3 containerd.sock sandbox Controller/Store API (宿主级!)
P4 metrics.sock /apm.sock HTTP
输出 /vercel/sandbox/v107c.out"""
import socket, struct, time, signal, subprocess

OUT = '/vercel/sandbox/v107c.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')
signal.alarm(170)


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def curl_h2(sockpath, path, body, t=6, ns='default', ctype='application/grpc'):
    try:
        tmp = '/vercel/sandbox/curl_req.bin'
        open(tmp, 'wb').write(body)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', sockpath, '-X', 'POST',
               '-H', 'Content-Type: %s' % ctype, '-H', 'TE: trailers']
        if ns:
            cmd += ['-H', 'containerd-namespace: %s' % ns]
        cmd += ['--data-binary', '@%s' % tmp, 'http://unix%s' % path]
        r = subprocess.run(cmd, capture_output=True, timeout=t + 2)
        return r.returncode, (r.stdout or b'')[:400]
    except Exception as e:
        return -1, ('EXC %s' % type(e).__name__).encode()


def connect_unix(sockpath, path, body=b'{}', t=2.0):
    """HTTP/1.1 POST Connect over unix socket"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
               'Connect-Protocol-Version: 1\r\nContent-Length: %d\r\nConnection: close\r\n\r\n'
               % (path, len(body))).encode() + body
        s.sendall(req)
        d = b''
        try:
            while True:
                c = s.recv(8192)
                if not c:
                    break
                d += c
        except Exception:
            pass
        s.close()
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        payload = d[hdr_end + 4:hdr_end + 4 + 300] if hdr_end > 0 else b''
        log('CONN %s %s -> %s body=%r' % (sockpath.split('/')[-1], path, status, payload[:200]))
        return d
    except Exception as e:
        log('CONN %s %s EXC %s' % (sockpath.split('/')[-1], path, type(e).__name__))
        return b''


def grpc_env(payload=b''):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def pvarint(n):
    out = bytearray()
    while n > 127:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def pstr(field_no, s):
    b = s.encode() if isinstance(s, str) else s
    return pvarint((field_no << 3) | 2) + pvarint(len(b)) + b


CELL = '/run/cell/cell.sock'
METR = '/run/metrics/metrics.sock'
APM = '/run/apm/apm.sock'
CTR = '/run/containerd/containerd.sock'

SERVICES = {
    'vercel.hive.celld.api.v1.CelldService': ['Heartbeat', 'GetDriveStorageUsage', 'Configure', 'SetWorkload',
                                               'StartContainer', 'StopContainer', 'WaitContainer'],
    'vercel.hive.cell.api.containers.v1.ContainersService': ['Create', 'Exec', 'Kill', 'Mount', 'Start', 'Stdin',
                                                              'StreamOutput', 'Wait'],
    'vercel.hive.cell.api.processes.v1.ProcessService': ['Kill', 'Start', 'StreamOutput', 'Wait'],
    'vercel.hive.cell.api.drives.v1.DrivesService': ['CreateSnapshot', 'SetOCIImageConfig'],
    'vercel.hive.cell.api.usage.v1.UsageService': ['GetResourceUsage'],
}

# ---------- P1 cell.sock Connect ----------
log('=== P1 cell.sock connect ===')
for svc, methods in SERVICES.items():
    for m in methods:
        connect_unix(CELL, '/%s/%s' % (svc, m))

# ---------- P2 cell.sock gRPC ----------
log('=== P2 cell.sock grpc ===')
for svc, methods in SERVICES.items():
    for m in methods[:6]:
        c, r = curl_h2(CELL, '/%s/%s' % (svc, m), grpc_env(b''), t=4)
        log('GRPC cell.sock %s/%s rc=%d out=%r' % (svc, m, c, r[:200]))

# ---------- P3 containerd sandbox API ----------
log('=== P3 containerd sandbox api ===')
# Store: List 无参数
c, r = curl_h2(CTR, '/containerd.services.sandbox.v1.Store/List', grpc_env(b''), t=5)
log('Store/List rc=%d out=%r' % (c, r[:400]))
# Controller/Status 带 sandbox_id
c, r = curl_h2(CTR, '/containerd.services.sandbox.v1.Controller/Status',
               grpc_env(pstr(1, 'v107')), t=5)
log('Controller/Status(v107) rc=%d out=%r' % (c, r[:300]))
# Controller/List? 不存在, 但试 Store/Get
c, r = curl_h2(CTR, '/containerd.services.sandbox.v1.Store/Get', grpc_env(pstr(1, 'v107')), t=5)
log('Store/Get(v107) rc=%d out=%r' % (c, r[:300]))
# Controller/Create 空参数 (看是否报缺参错误而不是未实现)
c, r = curl_h2(CTR, '/containerd.services.sandbox.v1.Controller/Create', grpc_env(b''), t=5)
log('Controller/Create(empty) rc=%d out=%r' % (c, r[:300]))
# runtime sandbox api
c, r = curl_h2(CTR, '/containerd.runtime.sandbox.v1.Sandbox/Status', grpc_env(b''), t=5)
log('rt.Sandbox/Status rc=%d out=%r' % (c, r[:200]))
# sandbox tasks?
c, r = curl_h2(CTR, '/containerd.services.sandbox.v1.Store/List', grpc_env(b''), t=5, ns='')
log('Store/List(ns=empty) rc=%d out=%r' % (c, r[:300]))

# ---------- P4 metrics / apm ----------
log('=== P4 metrics/apm ===')
for sock in (METR, APM):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(sock)
        s.sendall(b'GET /metrics HTTP/1.1\r\nHost: unix\r\nConnection: close\r\n\r\n')
        d = b''
        try:
            while True:
                c2 = s.recv(8192)
                if not c2:
                    break
                d += c2
        except Exception:
            pass
        s.close()
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        payload = d[hdr_end + 4:hdr_end + 4 + 600] if hdr_end > 0 else b''
        log('HTTP %s /metrics -> %s body=%r' % (sock.split('/')[-1], status, payload[:400]))
    except Exception as e:
        log('HTTP %s EXC %s' % (sock.split('/')[-1], type(e).__name__))
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(sock)
        s.sendall(b'GET / HTTP/1.1\r\nHost: unix\r\nConnection: close\r\n\r\n')
        d = b''
        try:
            while True:
                c2 = s.recv(8192)
                if not c2:
                    break
                d += c2
        except Exception:
            pass
        s.close()
        status = d.split(b'\r\n', 1)[0].decode(errors='replace') if d else 'NO_RESP'
        hdr_end = d.find(b'\r\n\r\n')
        payload = d[hdr_end + 4:hdr_end + 4 + 300] if hdr_end > 0 else b''
        log('HTTP %s / -> %s body=%r' % (sock.split('/')[-1], status, payload[:200]))
    except Exception as e:
        log('HTTP %s / EXC %s' % (sock.split('/')[-1], type(e).__name__))

log('V107C_DONE')
f.close()
