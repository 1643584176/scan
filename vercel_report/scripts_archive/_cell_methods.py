# -*- coding: utf-8 -*-
"""提取 celld/sandboxctrl 全部 RPC 方法名 + 错误模板"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')


def uniq(d, pats, lim=40):
    seen = set()
    for pat in pats:
        for m in re.finditer(pat, d):
            s = m.group().decode(errors='replace')
            if s not in seen:
                seen.add(s)
                print(s[:150])
            if len(seen) >= lim:
                return


def main():
    celld = open('/mnt/vdax/opt/vercel/celld', 'rb').read()
    sb = open('/mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/3/fs/opt/vercel/sandboxctrl', 'rb').read()
    print('===== celld DrivesService methods =====')
    uniq(celld, [rb'DrivesService/[A-Za-z_]+', rb'drivesv1\.[A-Za-z_]+', rb'DrivesService[A-Za-z_]*'])
    print('===== celld all service paths =====')
    uniq(celld, [rb'[A-Za-z0-9_.]+/[A-Za-z0-9_.]+Service/[A-Za-z_]+'], 60)
    print('===== celld host api refs =====')
    uniq(celld, [rb'[A-Za-z_/.-]*host[_-]?api[A-Za-z_/.-]*', rb'host/api/[A-Za-z_]+',
                 rb'HOST_[A-Z_]{3,30}', rb'[a-z-]*host[.-]?address[A-Za-z_]*'], 25)
    print('===== celld auth templates =====')
    uniq(celld, [rb'[A-Za-z %_]{8,80}not authorized[A-Za-z %_]{0,60}',
                 rb'[A-Za-z %_]{8,80}allowed[A-Za-z %_]{0,60}'], 25)
    print('===== sandboxctrl service methods =====')
    uniq(sb, [rb'[A-Za-z0-9_.]+Service/[A-Za-z_]+', rb'sandbox\.[A-Za-z_]+Request',
              rb'controllerv1\.[A-Za-z_]+Request'], 50)
    print('===== sandboxctrl bucket url =====')
    uniq(sb, [rb'[A-Za-z_ %]{4,60}bucket[A-Za-z_ %]{0,50}', rb'[A-Za-z_]{0,20}base_?url[A-Za-z_]{0,30}'], 20)


if __name__ == '__main__':
    main()
