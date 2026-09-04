# -*- coding: utf-8 -*-
"""在沙箱内 dump celld / sandboxctrl 二进制的关键字符串 (分析授权逻辑)"""
import re, os, sys
sys.stdout.reconfigure(encoding='utf-8')


def dump(p, pats, lim=30):
    print('###', p)
    try:
        d = open(p, 'rb').read()
        print('size', len(d))
        seen = set()
        n = 0
        for pat in pats:
            for m in re.finditer(pat, d):
                s = m.group().decode(errors='replace')
                if s in seen:
                    continue
                seen.add(s)
                print(s[:200])
                n += 1
                if n >= lim:
                    return
    except Exception as e:
        print('ERR', e)


def main():
    base = '/mnt/vdax'
    pats = [rb'[A-Za-z_]*base_url[A-Za-z_]*',
            rb'[A-Za-z_]*authorized[A-Za-z_]*',
            rb'[A-Za-z_]*snapshot[A-Za-z_]*',
            rb'[A-Za-z_]*drive[A-Za-z_]*']
    dump(base + '/opt/vercel/celld', pats, 40)
    for d in ['/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/6/fs/opt/vercel',
              '/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/3/fs/opt/vercel',
              '/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/4/fs/opt/vercel',
              '/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/2/fs/opt/vercel']:
        if os.path.isdir(base + d):
            print('### DIR', d, os.listdir(base + d))
            for f in os.listdir(base + d):
                fp = base + d + '/' + f
                if os.path.isfile(fp):
                    dump(fp, pats, 25)


if __name__ == '__main__':
    main()
