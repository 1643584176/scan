# -*- coding: utf-8 -*-
"""提取 celld/sandboxctrl 关键字符串的上下文 (授权逻辑/URL 构造)"""
import re, sys
sys.stdout.reconfigure(encoding='utf-8')


def ctx(p, needles, span=260, lim=10):
    d = open(p, 'rb').read()
    print('=====', p, 'size', len(d))
    for nd in needles:
        print('--- needle:', nd)
        n = 0
        for m in re.finditer(re.escape(nd.encode()), d):
            s = d[max(0, m.start() - span):m.end() + span]
            txt = ''.join(chr(b) if 32 <= b < 127 else ' ' for b in s)
            txt = re.sub(r'\s+', ' ', txt).strip()
            print(txt[:600])
            n += 1
            if n >= lim:
                break


def main():
    celld = '/mnt/vdax/opt/vercel/celld'
    sb = '/mnt/vdax/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/3/fs/opt/vercel/sandboxctrl'
    ctx(celld, ['allowed_snapshot_base_urls', 'not authorized for this drive',
                'base_url', 'CreateSnapshot', 'DrivesService'], 240, 8)
    ctx(sb, ['bucket_base_url', 'base_url', 'create_snapshot', 'CreateSnapshot',
             's3://', 'drive_id'], 240, 10)


if __name__ == '__main__':
    main()
