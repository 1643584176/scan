# -*- coding: utf-8 -*-
"""外部直连 endpoint 技术测试(psql 协议层,全新面)
矩阵:凭据 × endpoint 跨租户认证隔离 + SNI 路由混淆
只做认证 + select,零写操作"""
import psycopg, ssl, socket, sys

A_EP = 'ep-autumn-cherry-ay51mbqz.c-5.us-east-2.db.netlify.com'
B_EP = 'ep-cold-unit-ae9s4l3i.c-2.us-east-2.db.netlify.com'
A_OWN = ('netlifydb_owner', 'npg_MtTpnyk2LE4j')
A_RO = ('netlifydb_readonly', 'WCtJ-h-b7w82YMIaM598M75SV7uYVTCv')
B_OWN = ('netlifydb_owner', 'npg_TWUSd2Mavu7G')


def try_conn(label, host, port, user, pwd, db='netlifydb', hostaddr=None, timeout=10):
    kw = dict(host=host, port=port, user=user, password=pwd, dbname=db,
              connect_timeout=timeout, sslmode='require')
    if hostaddr:
        kw['hostaddr'] = hostaddr
    try:
        c = psycopg.connect(**kw)
        with c.cursor() as cur:
            cur.execute('select current_user, current_database(), version()')
            row = cur.fetchone()
            print('%-34s OK  %s | db=%s | %s' % (label, row[0], row[1], row[2][:50]))
        c.close()
    except psycopg.OperationalError as e:
        print('%-34s FAIL %s' % (label, str(e).strip()[:160]))
    except Exception as e:
        print('%-34s ERR  %s' % (label, str(e).strip()[:160]))


print('== 认证隔离矩阵 ==')
try_conn('A owner x A EP(基线)', A_EP, 5432, *A_OWN)
try_conn('A owner x B EP(跨租户)', B_EP, 5432, *A_OWN)
try_conn('B owner x A EP(反跨)', A_EP, 5432, *B_OWN)
try_conn('A readonly x A EP', A_EP, 5432, *A_RO)
try_conn('A readonly x B EP', B_EP, 5432, *A_RO)
try_conn('B owner x B EP(基线)', B_EP, 5432, *B_OWN)

print()
print('== SNI/路由混淆 ==')
# 1. TCP 到 A 的 IP,SNI 用 B 域名(psycopg: hostaddr=IP + host=B)
try:
    ip_a = socket.gethostbyname(A_EP)
    ip_b = socket.gethostbyname(B_EP)
    print('A IP=%s B IP=%s' % (ip_a, ip_b))
except Exception as e:
    print('resolve err', e)
try_conn('TCP A-IP + SNI B, A owner', B_EP, 5432, *A_OWN, hostaddr=ip_a)
try_conn('TCP B-IP + SNI A, A owner', A_EP, 5432, *A_OWN, hostaddr=ip_b)
try_conn('TCP B-IP + SNI A, B owner', A_EP, 5432, *B_OWN, hostaddr=ip_b)
