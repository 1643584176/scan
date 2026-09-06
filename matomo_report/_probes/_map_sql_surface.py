# -*- coding: utf-8 -*-
"""Map Matomo SQL-construction attack surface.

Step 1: where are DB calls made + which files build SQL strings with
variable interpolation (heuristic for injection-relevant spots).
"""
import os
import re

ROOT = r'F:\scan\matomo_report\_src\matomo'
SKIP = {'.git', 'node_modules', 'js', 'lang', 'libs', 'vendor',
        'tests', 'misc', '.github', 'config'}

DB_CALL = re.compile(r"->(query|fetchAll|fetchOne|fetchRow|fetchAssoc|fetch)\s*\(")
SQL_STR = re.compile(r"['\"](SELECT|INSERT|UPDATE|DELETE|REPLACE|WITH)\s+.*?['\"]\s*[.;,)]", re.S | re.I)
VAR_IN_SQL = re.compile(r"['\"]{1}[^'\"]*\$[A-Za-z_\[][^'\"]*['\"]", re.S)
SQL_KEYWORD = re.compile(r"(SELECT|INSERT INTO|UPDATE|DELETE FROM|REPLACE INTO)", re.I)

def walk():
    for dp, dns, fns in os.walk(ROOT):
        dns[:] = [d for d in dns if d not in SKIP]
        for fn in fns:
            if fn.endswith('.php'):
                yield os.path.join(dp, fn)

db_files = {}
sql_interp_files = {}
total_php = 0
total_lines = 0

for p in walk():
    total_php += 1
    try:
        with open(p, encoding='utf-8', errors='replace') as f:
            src = f.read()
    except OSError:
        continue
    total_lines += src.count('\n')
    rel = os.path.relpath(p, ROOT)
    ndb = len(DB_CALL.findall(src))
    if ndb:
        db_files[rel] = ndb
    # SQL string containing a $var inside the same string literal
    for m in SQL_KEYWORD.finditer(src):
        # crude: check line contains both SQL keyword and '$'
        line_start = src.rfind('\n', 0, m.start()) + 1
        line_end = src.find('\n', m.start())
        line = src[line_start:line_end if line_end != -1 else len(src)]
        if '$' in line and ('"' in line or "'" in line):
            sql_interp_files.setdefault(rel, 0)
            sql_interp_files[rel] += 1

print('total php files: %d, lines: %d' % (total_php, total_lines))
print()
print('== files with DB calls: %d files ==' % len(db_files))
for rel, n in sorted(db_files.items(), key=lambda x: -x[1])[:40]:
    print('%4d  %s' % (n, rel))
print()
print('== files with SQL keyword + $var on same line: %d files ==' % len(sql_interp_files))
for rel, n in sorted(sql_interp_files.items(), key=lambda x: -x[1])[:50]:
    print('%4d  %s' % (n, rel))
