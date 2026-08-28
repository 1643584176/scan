# -*- coding: utf-8 -*-
"""Phase24: guest 环境完整侦察 - 进程/挂载/capabilities/主机名/设备"""
import sys, time, re
sys.path.insert(0, r'D:\scan\skills\non-traditional-vuln-hunting')
from fw_driver import api, cmd, TEAM, fresh_sandbox_deny_all

GUEST = r'''
import os, glob, socket, subprocess

def show(label, data):
    print('[%s] %s' % (label, data[:700].replace(chr(10), ' || ')), flush=True)

# 主机名/内核
show('hostname', open('/proc/sys/kernel/hostname').read())
show('uname', str(os.uname()))
# 进程列表 (PID 命名空间隔离?)
pids = sorted(int(d) for d in os.listdir('/proc') if d.isdigit())
show('pids', str(pids[:60]))
cmds = {}
for pid in pids[:40]:
    try:
        c = open('/proc/%d/cmdline' % pid, 'rb').read().replace(b'\x00', b' ').decode()[:80]
        cmds[pid] = c
    except Exception:
        pass
show('proc-cmds', str(cmds))
# 挂载
show('mounts', open('/proc/self/mountinfo').read())
# capabilities
try:
    show('capEff', [l for l in open('/proc/self/status') if l.startswith('Cap')])
except Exception as e:
    show('cap-err', str(e))
# 网络
show('if_inet6', open('/proc/net/if_inet6').read())
show('hosts', open('/etc/hosts').read())
show('resolv', open('/etc/resolv.conf').read())
show('route', open('/proc/net/route').read())
# 目录
for d in ['/vercel', '/home', '/home/vercel-sandbox', '/run', '/var/run', '/tmp', '/opt', '/etc']:
    try:
        show('ls-' + d, str(os.listdir(d)))
    except Exception as e:
        show('ls-' + d, 'ERR ' + str(e))
# 设备
try:
    show('dev', str(os.listdir('/dev'))[:400])
except Exception as e:
    show('dev', 'ERR ' + str(e))
# 环境变量
try:
    show('env', subprocess.run(['env'], capture_output=True, text=True).stdout)
except Exception as e:
    show('env', 'ERR ' + str(e))
print('done', flush=True)
'''
code = "cat > /tmp/pg32.py <<'PYEOF'\n" + GUEST + "\nPYEOF\npython3 /tmp/pg32.py"

SID = "sbx_aCiW8kdYJwYLOY6KpXlqUrUqNEfq"  # fwtest11

if __name__ == "__main__":
    c, r = cmd(SID, "bash", ["-lc", code], timeout_ms=90000)
    print('cmd:', c, flush=True)
    print(r[:9000], flush=True)
