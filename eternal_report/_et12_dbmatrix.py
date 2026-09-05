# -*- coding: utf-8 -*-
"""ET12: DB/internal-service subdomain matrix DNS probe (read-only DNS, no HTTP)"""
import socket, threading

NAMES = [
    "db", "database", "databases", "sql", "query", "queries", "mysql", "postgres",
    "postgresql", "pg", "pgadmin", "adminer", "phpmyadmin", "dba", "dbs", "db1",
    "db2", "db-prod", "db-main", "analytics", "warehouse", "report", "reports",
    "bi", "metabase", "superset", "grafana", "kibana", "es", "elastic", "redis",
    "mongo", "mongodb", "cassandra", "api-db", "data", "dataservice", "internal",
    "internal-api", "api-internal", "gateway", "gw", "admin", "admin-api", "backend",
    "backend-api", "service", "services", "core", "api2", "api3", "search", "autocomplete",
]
DOMAINS = [
    "zomato.com", "runnr.in", "zomans.com", "district.in", "edition.in",
    "ticketnew.com", "tktnew.com", "insider.in", "blinkit.com", "hyperpure.com",
    "eternal.com", "grofers.com", "grofer.io", "zdev.net",
]
SKIP = {  # already known/irrelevant
    "api2.grofers.com", "api.grofers.com", "api.edition.in", "api-internal.edition.in",
    "jumbo.edition.in", "link.district.in", "cdn.district.in", "b.zmtcdn.com",
}

def check(n, d):
    h = "%s.%s" % (n, d)
    if h in SKIP:
        return None
    try:
        infos = socket.getaddrinfo(h, 443, socket.AF_INET, socket.SOCK_STREAM)
        return (h, infos[0][4][0])
    except Exception:
        return None

def main():
    jobs = [(n, d) for n in NAMES for d in DOMAINS]
    found = []
    lock = threading.Lock()
    def worker(j):
        r = check(*j)
        if r:
            with lock:
                found.append(r)
    threads = []
    for j in jobs:
        t = threading.Thread(target=worker, args=(j,), daemon=True)
        t.start()
        threads.append(t)
        if len(threads) >= 64:
            for t in threads:
                t.join(30)
            threads = []
    for t in threads:
        t.join(30)
    print("== DB/internal subdomain hits (%d checks) ==" % len(jobs))
    for h, ip in sorted(found):
        print("%-45s %s" % (h, ip))
    print("done %d found" % len(found), flush=True)

if __name__ == "__main__":
    main()
