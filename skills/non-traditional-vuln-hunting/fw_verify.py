# -*- coding: utf-8 -*-
"""D 项闭环验证: 创建时传 deny-all vs update 端点设置 deny-all
1) 沙箱 denycreate: 创建 body 带 networkPolicy deny-all -> 查详情字段 -> 跑 udp_bypass
2) 沙箱 denyupd: 创建默认 -> POST /v2/sandboxes/sessions/{sid}/network-policy deny-all -> 查详情字段 -> 跑 udp_bypass
3) 对照结论写入 out/fw_verify_*.txt
"""
import base64, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vercel_driver import api, cmd, fresh_sandbox, TEAM, PROJ

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(os.path.dirname(HERE), 'out')


def get_detail(name):
    c, r = api("GET", "/v2/sandboxes/%s?teamId=%s&projectId=%s" % (name, TEAM, PROJ))
    return c, r


def set_policy(sid, mode):
    body = {"mode": mode}
    c, r = api("POST", "/v2/sandboxes/sessions/%s/network-policy?teamId=%s" % (sid, TEAM), body)
    return c, r


def inject_and_run(sid, guest_name, outfile, marker, run_timeout_ms=150000, wait_rounds=8):
    code = open(os.path.join(HERE, guest_name), 'rb').read()
    payload = base64.b64encode(code).decode()
    script_name = guest_name.replace('.py', '.py')
    inject = "import base64;open('/vercel/sandbox/%s','wb').write(base64.b64decode('%s'))" % (script_name, payload)
    c, r = cmd(sid, 'python3', ['-c', inject], timeout_ms=30000)
    print('  [inject %s] %d' % (script_name, c), flush=True)
    time.sleep(1)
    c, r = cmd(sid, 'python3', ['/vercel/sandbox/' + script_name], timeout_ms=run_timeout_ms)
    print('  [run %s] %d %s' % (script_name, c, r[:200].replace('\n', ' ')), flush=True)
    time.sleep(1)
    for attempt in range(wait_rounds):
        time.sleep(3)
        c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + outfile], timeout_ms=30000)
        if c == 200 and marker in r:
            print('  [done %s] round=%d len=%d' % (script_name, attempt, len(r)), flush=True)
            return r
        print('  [wait %s] r%d status=%d' % (script_name, attempt, c), flush=True)
    c, r = cmd(sid, 'cat', ['/vercel/sandbox/' + outfile], timeout_ms=30000)
    return r if c == 200 else ('(no output) status=%d' % c)


def save(fn, txt):
    p = os.path.join(OUTDIR, fn)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(txt)
    print('saved ->', p, flush=True)


GUEST = 'udp_bypass_guest.py'
OUTF = 'udpbypass.out'
MARK = 'UDPBYPASS_DONE'

# ---- 沙箱 A: 创建时传 deny-all ----
print('===== A: denycreate (创建 body 带 networkPolicy deny-all) =====', flush=True)
try:
    sidA = fresh_sandbox('denycreate', network_mode='deny-all')
    print('sidA:', sidA, flush=True)
    time.sleep(2)
    cA, rA = get_detail('denycreate')
    print('detail A:', cA, rA[:800], flush=True)
    save('fw_verify_A_create_detail.txt', 'status=%d\n%s' % (cA, rA))
    resA = inject_and_run(sidA, GUEST, OUTF, MARK)
    save('fw_verify_A_udp_bypass.txt', resA)
except Exception as e:
    print('A EXC:', e, flush=True)
    save('fw_verify_A_EXC.txt', str(e))

# ---- 沙箱 B: update 端点设置 deny-all ----
print('===== B: denyupd (创建默认 -> update policy deny-all) =====', flush=True)
try:
    sidB = fresh_sandbox('denyupd', network_mode='allow-all')
    print('sidB:', sidB, flush=True)
    cB0, rB0 = set_policy(sidB, 'deny-all')
    print('set_policy B:', cB0, rB0[:400], flush=True)
    time.sleep(2)
    cB, rB = get_detail('denyupd')
    print('detail B:', cB, rB[:800], flush=True)
    save('fw_verify_B_update_detail.txt', 'set_policy_status=%d\n%s\ndetail_status=%d\n%s' % (cB0, rB0, cB, rB))
    resB = inject_and_run(sidB, GUEST, OUTF, MARK)
    save('fw_verify_B_udp_bypass.txt', resB)
except Exception as e:
    print('B EXC:', e, flush=True)
    save('fw_verify_B_EXC.txt', str(e))

print('=== FW VERIFY ALL DONE ===', flush=True)
