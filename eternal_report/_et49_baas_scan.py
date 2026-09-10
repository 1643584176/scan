# -*- coding: utf-8 -*-
"""ET49: scan Eternal JS bundles for BaaS/direct-DB fingerprints & keys (no shell quoting issues)"""
import os, re, glob

JS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
files = glob.glob(os.path.join(JS_DIR, "*.js"))

pats = {
    "baas": re.compile(r'(firebaseio\.com|firebaseapp\.com|supabase\.co|appwrite|pocketbase|realm\.mongodb|mongodb\+srv|blob\.core\.windows\.net)', re.I),
    "s3": re.compile(r'(s3[a-z0-9.-]*\.amazonaws\.com|storage\.googleapis\.com|[a-z0-9._-]+\.s3\.amazonaws\.com)', re.I),
    "dburl": re.compile(r'(postgres(?:ql)?://|mysql://|redis://|mongodb://|amqp://)[^\s"\'<>]{6,120}', re.I),
    "key": re.compile(r'(?:api[_-]?key|access[_-]?token|client[_-]?secret|x-api-key|secret[_-]?key|auth[_-]?key)["\']?\s*[:=]\s*["\']([^"\']{10,90})["\']', re.I),
    "elastic": re.compile(r'([a-z0-9.-]+:9200|[a-z0-9.-]+:5601|elasticsearch|opensearch)', re.I),
}

hits = {}
for fn in files:
    try:
        data = open(fn, "r", encoding="utf-8", errors="replace").read()
    except Exception:
        continue
    for typ, rx in pats.items():
        for m in rx.finditer(data):
            s = m.group(0)[:150].replace("\n", " ")
            hits.setdefault((typ, s), set()).add(os.path.basename(fn))

for typ in ("baas", "s3", "dburl", "elastic", "key"):
    print("==== %s ====" % typ.upper())
    for (t, s), fns in sorted(hits.items()):
        if t != typ:
            continue
        print("%-130s %s" % (s, ",".join(sorted(fns)[:3])))
    print()
print("done", flush=True)
