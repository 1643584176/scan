# -*- coding: utf-8 -*-
# 从 vda27 生成 vda28: 修正 containerd.sock 路径 + 增加 init.sock/metrics.sock 探测
src = open('skills/non-traditional-vuln-hunting/vda27_ctrd_probe_guest.py', encoding='utf-8').read()
src = src.replace('vda27_ctrd_probe', 'vda28_ctrd2').replace('V27N_DONE', 'V28O_DONE').replace('v27n.out', 'v28o.out')
src = src.replace("csp = '/mnt/vdax/run/cell/containerd.sock'", "csp = '/mnt/vdax/run/containerd/containerd.sock'")
extra = '''
    # P2b: init.sock / metrics.sock / apm.sock 探测
    log('=== P2b other socks ===')
    for spath, tag in [('/mnt/vdax/volumes/run/vercel/share/init.sock', 'init'),
                       ('/mnt/vdax/run/metrics/metrics.sock', 'metrics'),
                       ('/mnt/vdax/run/apm/apm.sock', 'apm')]:
        try:
            st = os.stat(spath)
            log('%s.sock exists mode=%o' % (tag, st.st_mode & 0o777))
        except Exception as e:
            log('%s.sock ERR %s' % (tag, e))
            continue
        for probe in ['/vercel.hive.cell.api.containers.v1.ContainersService/List',
                      '/containerd.services.containers.v1.Containers/List',
                      '/containerd.services.images.v1.Images/List',
                      '/grpc.health.v1.Health/Check']:
            st2, bd2 = rpc_raw(spath, probe, grpc_env(b''), t=3)
            log('%s %-60s -> %s | %s' % (tag, probe, st2, bd2[:200].replace('\\n', ' ')))
            time.sleep(0.1)

'''
src = src.replace("    # P3: cell.sock 对照 (确认两个 socket 不同服务)", extra + "    # P3: cell.sock 对照 (确认两个 socket 不同服务)")
open('skills/non-traditional-vuln-hunting/vda28_ctrd2_guest.py', 'w', encoding='utf-8').write(src)

# 驱动
src2 = open('_run_v19f.py', encoding='utf-8').read()
src2 = src2.replace('v19f', 'v28o').replace('vda19_exec_chain_guest.py', 'vda28_ctrd2_guest.py').replace('V19F_DONE', 'V28O_DONE')
open('_run_v28o.py', 'w', encoding='utf-8').write(src2)
print('gen ok')
