# -*- coding: utf-8 -*-
"""生成 logs 英文副本: 将 data 字段中的中文阶段标记替换为英文 (数据不变)"""
import os, re

SRC = r'F:\scan\vercel_report\fw_vpc'

# (源文件, 输出文件, [(中文标记, 英文标记)])
JOBS = [
    ('fwcustom5_fw_vpc_deep_guest_20260829_153539.txt', 'fw_vpc_deep_125_125_en.txt', [
        ('P1 PG banner (12 采样)', 'P1 PG banner (12 samples)'),
        ('P2 sandbox 特征端口 (8 IP x 5 端口)', 'P2 sandbox characteristic ports (8 IPs x 5 ports)'),
        ('P3 扩展子网 5432 采样', 'P3 extended-subnet 5432 sampling'),
        ('P4 DNS 特殊查询', 'P4 DNS special queries'),
    ]),
    ('fwcustom5_fw_pg_fp_guest_20260829_154040.txt', 'fw_pg_fp_rst_en.txt', [
        ('P1 PG StartupMessage 指纹 (9 采样)', 'P1 PG StartupMessage fingerprint (9 samples)'),
        ('P2 对照: 无服务端口', 'P2 control: no-service ports'),
        ('P3 对照: 本沙箱 localhost 5432 (应拒绝)', 'P3 control: this-sandbox localhost 5432 (should be denied)'),
    ]),
    ('fwcustom5_fw_pg_tls_guest_20260829_154254.txt', 'fw_pg_tls_eof_en.txt', [
        ('P1 TLS PG StartupMessage (9 采样)', 'P1 TLS PG StartupMessage (9 samples)'),
    ]),
    ('denyall3_fw_vpc_deny_guest_20260829_153409.txt', 'denyall3_all113_en.txt', [
        ('P1 已知 PG IP x 5432 (deny-all)', 'P1 known PG IPs x 5432 (deny-all)'),
        ('P2 172.31.0.0/24 x 5432 并行', 'P2 172.31.0.0/24 x 5432 parallel'),
        ('P3 172.31.0.2 端口采样', 'P3 172.31.0.2 port sampling'),
        ('P4 公网对照', 'P4 public control'),
    ]),
]

for src, dst, pairs in JOBS:
    p = os.path.join(SRC, src)
    txt = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in txt, 'MISSING %r in %s' % (old, src)
        txt = txt.replace(old, new)
    out = os.path.join(SRC, dst)
    open(out, 'w', encoding='utf-8').write(txt)
    # 校验无中文残留
    cjk = re.findall(r'[\u4e00-\u9fff]+', txt)
    print(dst, 'OK' if not cjk else ('STILL-CJK: %s' % cjk), flush=True)
print('DONE')
