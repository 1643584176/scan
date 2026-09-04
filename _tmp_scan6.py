# -*- coding: utf-8 -*-
"""批量打印名字敏感但未命中凭证模式的文件头部,用于快速甄别。"""
import io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

targets = [
    r'neon_report\_pg_authid_dump.json',
    r'netlify_report\_dbq_report-pg_authid-leak.md',
    r'figma_report\_figma_creds.py',
    r'netlify_report\_net_creds.py',
    r'netlify_report\_net_cred_x.py',
    r'netlify_report\_chk_creds.py',
    r'neon_report\_chk_creds_struct.py',
    r'neon_report\_f2_cred_schema.py',
    r'neon_report\_f3_cred_tests.py',
    r'neon_report\_m8f_cred_schema.py',
    r'neon_report\_p1_cred_scope.py',
    r'_wh_uuid.txt',
    r'figma_report\_figma_har_analysis.txt',
    r'figma_report\_lg_enum3.txt',
    r'netlify_report\_st_tid.json',
    r'netlify_report\_auth_better_auth.json',
    r'neon_report\_na_tokens.json',
    r'neon_report\_neonauth_priv.txt',
    r'supabase_report\_sb42_authacl.txt',
    r'netlify_report\_probe1_full.txt',
    r'netlify_report\_chk_tokena.py',
    r'netlify_report\_chk_tokens.py',
    r'netlify_report\_dbq_tokenB.py',
    r'netlify_report\_idn_jwt_probe.py',
    r'neon_report\_da3_jwt_forge.py',
    r'neon_report\_j19_setcookie_audit.py',
    r'neon_report\_j4_jwt_get.py',
    r'_aic_sess1.py',
    r'_aic_login_pccp_out.txt',
    r'neon_report\_ctx_b.json',
]
for rel in targets:
    fp = os.path.join(r'D:\scan', rel.replace('/', os.sep))
    print('=' * 20, rel)
    if not os.path.isfile(fp):
        print('  (missing)')
        continue
    try:
        with open(fp, 'r', encoding='utf-8', errors='replace') as f:
            for i, ln in enumerate(f):
                if i >= 10:
                    break
                print('  ' + ln.rstrip()[:150])
    except Exception as e:
        print('  read-fail', e)
