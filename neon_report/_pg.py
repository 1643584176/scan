# -*- coding: utf-8 -*-
"""Shared PG connection helper (pg8000) for neon staging data plane."""
import ssl
import pg8000.dbapi

_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE


def connect(host, user, password, db="neondb", port=5432, timeout=15):
    return pg8000.dbapi.connect(host=host, user=user, password=password,
                                database=db, port=port, timeout=timeout,
                                ssl_context=_ctx)


def query(conn, sql, params=None):
    cur = conn.cursor()
    try:
        cur.execute(sql, params or ())
    except Exception:
        conn.rollback()
        raise
    try:
        return cur.fetchall()
    except Exception:
        conn.commit()
        return []


def exec_(conn, sql, params=None):
    cur = conn.cursor()
    try:
        cur.execute(sql, params or ())
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e


def one(conn, sql, params=None):
    rows = query(conn, sql, params)
    return rows[0] if rows else None
