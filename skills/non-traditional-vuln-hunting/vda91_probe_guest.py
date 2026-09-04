# -*- coding: utf-8 -*-
"""v91 payload: (a) attachedOutputReader 深挖 (b) StdinRequest 字段 (c) SO 并发保持连接测试
v90 F 发现: SO-before-start 挂起 4s(超时断开) 而非立即报错; Start 后 SO 立即报 attach 错误
v91 假设: StreamOutput handler 在未 attach/未启动时阻塞等待; 正确时序可能 =
         Create → SO 保持连接打开 → Start → Exec → 数据推送到已建立的流
(c) SO 线程保持连接: Create(attachStdin:true) → SO(stream1) 保持 → Start → Exec → 检查数据
(c2) 无 attach 对照: Create → SO 保持 → Start → Exec → 检查
(c3) stderr: Create(attachStdin:true) → SO(stream2) 保持 → Start → Exec → 检查
(d) Stdin bidi: Create(attachStdin:true) → Stdin 流保持 → Start → Exec → 检查 Stdin 流数据
(e) SO 长连接不 Start 观察
"""
import socket, time, os, json, re, struct, threading

OUT = '/vercel/sandbox/v91c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v91c2.out'):
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass


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


def pvar(field_no, n):
    return pvarint((field_no << 3) | 0) + pvarint(n)


def rpc_raw(path, body=b'', ct='application/json', t=4):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect('/run/cell/cell.sock')
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: %s\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n' % (path, ct, len(body)))
        s.sendall(req.encode() + body)
        data = b''
        while True:
            try:
                chunk = s.recv(8192)
            except socket.timeout:
                break
            if not chunk:
                break
            data += chunk
        s.close()
        if not data:
            return 'NORESP', '', b''
        head, _, rest = data.partition(b'\r\n\r\n')
        lines = head.decode(errors='replace').split('\r\n')
        return lines[0], '\n'.join(lines[1:])[:100], rest
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, '', b''


def rpc(path, body='{}', t=3):
    st, hd, bd = rpc_raw(path, body.encode(), 'application/json', t)
    return st, bd[:600].decode(errors='replace')


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def grpc_req(pl):
    return b'\x00' + struct.pack('>I', len(pl)) + pl


class Keep:
    """保持连接: 后台线程发请求并持续读, 1s 轮询 stop"""
    def __init__(self, path, body, t=20):
        self.path, self.body, self.t = path, body, t
        self.data = bytearray()
        self.done = threading.Event()
        self._stop = threading.Event()
        self._err = None
        self._t = threading.Thread(target=self._run)
        self._t.daemon = True

    def _run(self):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect('/run/cell/cell.sock')
            req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/grpc\r\n'
                   'Content-Length: %d\r\nConnection: keep-alive\r\n\r\n' % (self.path, len(self.body)))
            s.sendall(req.encode() + self.body)
            deadline = time.time() + self.t
            while not self._stop.is_set() and time.time() < deadline:
                try:
                    chunk = s.recv(8192)
                except socket.timeout:
                    continue
                except OSError:
                    break
                if not chunk:
                    break
                self.data += chunk
            try:
                s.close()
            except Exception:
                pass
        except Exception as e:
            self._err = e
        self.done.set()

    def start(self):
        self._t.start()
        return self

    def stop(self):
        self._stop.set()

    def status(self):
        return 'done=%s err=%s data=%d' % (self.done.is_set(), self._err, len(self.data))


def main():
    log('V91 payload start pid=%d' % os.getpid())
    R = '/proc/1/root'
    data = open(R + '/opt/vercel/celld', 'rb').read()

    # A. attachedOutputReader 深挖
    idxs = [m.start() for m in re.finditer(rb'attachedOutputReader', data)]
    log('A1 attachedOutputReader count=%d idx=%s' % (len(idxs), idxs[:10]))
    seen_ctx = set()
    for i in idxs[:6]:
        seg = data[max(0, i - 250):i + 250]
        syms = re.findall(rb'[A-Za-z_][A-Za-z0-9_.]{4,70}', seg)
        line = ' | '.join(s.decode(errors='replace')[:70] for s in syms[:12])
        if line not in seen_ctx:
            seen_ctx.add(line)
            log('A1CTX@%d: %s' % (i, line))
    methods = sorted(set(m.group(1).decode() for m in re.finditer(rb'\(\*attachedOutputReader\)\.([A-Za-z0-9_]+)', data)))
    log('A2 attachedOutputReader methods: %s' % methods)
    funcs = sorted(set(m.group(0).decode(errors='replace') for m in re.finditer(rb'(?:func )?[A-Za-z0-9_\.]*AttachedOutput[A-Za-z0-9_\.]*', data)))
    log('A2b AttachedOutput funcs: %s' % funcs[:20])
    strs = set()
    for m in re.finditer(rb'[A-Za-z0-9_]*[Aa]ttach[A-Za-z0-9_]*', data):
        s = m.group().decode(errors='replace')
        if 3 <= len(s) <= 60:
            strs.add(s)
    log('A3 attach strings (%d): %s' % (len(strs), sorted(strs)[:40]))
    errs = []
    for m in re.finditer(rb'must be attached', data):
        i = m.start()
        seg = data[max(0, i - 80):i + 150]
        errs.append(re.findall(rb'[\x20-\x7e]{4,}', seg)[:1])
    log('A4 must-be-attached errs: %s' % errs[:6])
    i = data.find(b'must be attached before start')
    if i > 0:
        seg = data[max(0, i - 600):i + 300]
        syms = re.findall(rb'[A-Za-z_][A-Za-z0-9_.]{5,80}', seg)
        log('A5 err-ctx: %s' % ' | '.join(s.decode(errors='replace')[:70] for s in syms[:16]))

    # B. StdinRequest / MountRequest 字段
    for mname in ('StdinRequest', 'MountRequest', 'AttachRequest', 'CreateTaskWithStdin'):
        pat = re.compile(rb'containers\.\(\*' + re.escape(mname.encode()) + rb'\)\.Get([A-Za-z0-9_]+)')
        got = sorted(set(m.group(1).decode() for m in pat.finditer(data)))
        log('B GET %s: %s' % (mname, got))

    # C. SO 并发保持连接测试
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    def create(body, tag):
        st, bd = rpc(CTR + '/Create', body, t=8)
        cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
        log('%s CREATE -> %s cid=%s' % (tag, st, cid or bd[:120]))
        return cid

    def so_hold_test(tag, body, stream, argv, wait=3.5):
        cid = create(body, tag)
        if not cid:
            return
        pl = pstr(1, cid) + pvar(2, stream)
        k = Keep(CTR + '/StreamOutput', grpc_req(pl)).start()
        time.sleep(1.5)
        log('%s SO-open: %s' % (tag, k.status()))
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(0.5)
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        log('%s execA -> %s' % (tag, bd[:90]))
        time.sleep(wait)
        log('%s SO-after: %s raw=%r' % (tag, k.status(), bytes(k.data)[:600]))
        k.stop()
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('%s killed' % tag)
        time.sleep(0.5)

    so_hold_test('C1', '{"drive_id":"sandbox","attachStdin":true}', 1,
                 ['/bin/sh', '-c', 'echo V91_C1_OUT_ABC123; echo V91_C1_ERR_XYZ789 >&2; sleep 5'])
    so_hold_test('C2', '{"drive_id":"sandbox"}', 1,
                 ['/bin/sh', '-c', 'echo V91_C2_OUT_ABC123; sleep 5'])
    so_hold_test('C3', '{"drive_id":"sandbox","attachStdin":true}', 2,
                 ['/bin/sh', '-c', 'echo V91_C3_ERR_XYZ789 >&2; sleep 5'])

    # D. Stdin bidi 流测试
    cid = create('{"drive_id":"sandbox","attachStdin":true}', 'D1')
    if cid:
        pl = pstr(1, cid)
        k = Keep(CTR + '/Stdin', grpc_req(pl)).start()
        time.sleep(1.5)
        log('D1 Stdin-open: %s' % k.status())
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(0.5)
        st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', 'echo V91_D1_OUT_DEF456; echo V91_D1_ERR_UVW000 >&2; sleep 5'], t=6)
        log('D1 execA -> %s' % bd[:90])
        time.sleep(3.5)
        log('D1 Stdin-after: %s raw=%r' % (k.status(), bytes(k.data)[:600]))
        k.stop()
        pl2 = pstr(1, cid) + pvar(2, 1)
        st, hd, bd = rpc_raw(CTR + '/StreamOutput', grpc_req(pl2), 'application/grpc', t=4)
        log('D1 SO-late -> %s %r' % (st, bd[:220]))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('D1 killed')
        time.sleep(0.5)

    # E. SO 长连接不 Start 观察
    cid = create('{"drive_id":"sandbox"}', 'E1')
    if cid:
        pl = pstr(1, cid) + pvar(2, 1)
        k = Keep(CTR + '/StreamOutput', grpc_req(pl), t=10).start()
        for i in range(3):
            time.sleep(2)
            log('E1 SO@%ds: %s raw=%r' % ((i + 1) * 2, k.status(), bytes(k.data)[:200]))
            if k.done.is_set():
                break
        k.stop()
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('E1 killed')

    log('V91C_DONE')


main()
