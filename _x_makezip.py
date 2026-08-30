# -*- coding: utf-8 -*-
"""重新打包完整 PoC zip: 复现脚本 + 全部证据输出 + 归因脚本 + 提交版报告"""
import os, sys, zipfile, time

SRC = r'F:\scan\vercel_report\fw_vpc'
OUT = os.path.join(SRC, 'fw_vpc_poc.zip')

# (源文件, zip 内路径)
files = [
    # 复现脚本 (最小化)
    ('_repro_min.py', '_repro_min.py'),
    # 四阶段同沙箱对照
    ('allowcmp_switch_p1_allowall.txt', 'logs/allowcmp_p1_allowall.txt'),
    ('allowcmp_switch_p2_custom.txt', 'logs/allowcmp_p2_custom.txt'),
    ('allowcmp_switch_p3_denyall.txt', 'logs/allowcmp_p3_denyall.txt'),
    ('allowcmp_switch_p4_custom_again.txt', 'logs/allowcmp_p4_custom_again.txt'),
    # 私有网段测绘 + 对照
    ('cidr1_cidr_probe_guest_20260829_162217.txt', 'logs/cidr1_custom_15open.txt'),
    ('cidr2_cidr_probe_guest_20260829_162341.txt', 'logs/cidr2_allowall_15x113.txt'),
    ('fwcustom5_fw_custom4b_guest_20260829_152804.txt', 'logs/fw_custom4b_35ip_bS.txt'),
    ('fw_vpc_deep_125_125_en.txt', 'logs/fw_vpc_deep_125_125.txt'),
    ('fw_pg_fp_rst_en.txt', 'logs/fw_pg_fp_rst.txt'),
    ('fw_pg_tls_eof_en.txt', 'logs/fw_pg_tls_eof.txt'),
    ('denyall3_all113_en.txt', 'logs/denyall3_all113.txt'),
    ('cidr1_http_probe_guest_20260829_162416.txt', 'logs/http_probe_nodata.txt'),
    ('mmds1_mmds_probe_guest_20260829_162042.txt', 'logs/mmds1_dns_refused.txt'),
    ('fw_custom3_allowall.txt', 'logs/fw_custom3_allowall.txt'),
    ('fw_custom3_custom.txt', 'logs/fw_custom3_custom.txt'),
    # 归因脚本 (nline_evidence, 英文注释版)
    ('nline_evidence/_x_nfinal4_en.py', 'attribution/_x_nfinal4.py'),
    ('nline_evidence/_x_nmulti_en.py', 'attribution/_x_nmulti.py'),
    ('nline_evidence/_x_nmatrix_en.py', 'attribution/_x_nmatrix.py'),
    ('nline_evidence/_x_cidr_en.py', 'attribution/_x_cidr.py'),
    ('nline_evidence/_x_e5repro_en.py', 'attribution/_x_e5repro.py'),
    # 提交版报告 (全英文)
    ('H1-sandbox-custom-policy-vpc-bypass-submission.md', 'REPORT-submission.md'),
    ('H1-sandbox-custom-policy-vpc-bypass-full-en.md', 'REPORT-full.md'),
]

with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for src, dst in files:
        p = os.path.join(SRC, src)
        if not os.path.exists(p):
            print('MISSING:', src, flush=True)
            continue
        z.write(p, dst)
        print('add:', dst, os.path.getsize(p), flush=True)
    # README
    readme = """Vercel Sandbox custom-policy private-range bypass - PoC evidence
=====================================================================
1. _repro_min.py      - minimal repro (TCP connect + PG SSLRequest)
2. logs/              - raw outputs (same-sandbox 4-phase switch + sampling)
3. attribution/       - policy-field attribution scripts (deniedCIDRs fail-open, allowedCIDRs reversal)
4. REPORT-*.md        - submission + full report
Team: team_GIy1SZ444lspqeNbh4r8uAUg
Project: prj_iyw2xfjP3RKPT7n8b8c1tBIxxK5F
Compliance: TCP connect + 8B handshake only, no auth, no data read.
"""
    z.writestr('README.txt', readme)
    print('add: README.txt', flush=True)

print('DONE ->', OUT, os.path.getsize(OUT), 'bytes', flush=True)
