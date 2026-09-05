# -*- coding: utf-8 -*-
"""ET6: download ticketnew-web + district-web JS chunks, extract API endpoints"""
import http.client, ssl, re, os, json

ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_js")
os.makedirs(OUT, exist_ok=True)


def get(h, path, maxread=4000000):
    conn = http.client.HTTPSConnection(h, 443, timeout=20, context=ctx)
    conn.request("GET", path, headers={"User-Agent": UA, "Accept": "*/*"})
    r = conn.getresponse()
    raw = r.read(maxread)
    conn.close()
    return r.status, raw


def page_js(path):
    st, raw = get("ticketnew.com", path)
    if st != 200:
        print("page fail", path, st)
        return []
    body = raw.decode("utf-8", "replace")
    return re.findall(r'<script[^>]+src="([^"]+)"', body)


def main():
    # buildManifest gives route->chunk mapping; grab ticketnew page routes first
    st, raw = get("cdn.district.in", "/ticketnew-web/_next/static/PG5bsPkEbSTO8eL6Hug-W/_buildManifest.js")
    if st == 200:
        b = raw.decode("utf-8", "replace")
        fn = os.path.join(OUT, "ticketnew_buildManifest.js")
        open(fn, "w", encoding="utf-8").write(b)
        routes = re.findall(r'"(/[^"]*)"', b)
        print("ticketnew routes (%d):" % len(routes))
        for r_ in sorted(set(routes))[:120]:
            print("  ", r_)
        print()

    jobs = []
    # ticketnew chunk list from earlier
    tn_srcs = ["https://cdn.district.in/ticketnew-web/_next/static/chunks/441p0qgf1a-ej.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/30tf0ncqwkhct.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/2aoz8lvlm7mvq.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/41e6-otdg16ql.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/0y2e4eauahyyk.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/turbopack-2489ptvbk5zgy.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/1l8-_u115gcxv.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/41p6l24qifb-y.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/44s4ft8a1mq01.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/45671znofo_bp.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/3zt3yadht-2bm.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/0xgedrw7kcn2n.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/2y4mfgfvzp7_r.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/0cdekd3-o6xsw.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/366kcpms-kj59.js",
               "https://cdn.district.in/ticketnew-web/_next/static/chunks/turbopack-09flq79c3w2ze.js"]
    for u in tn_srcs:
        jobs.append(("cdn.district.in", u.replace("https://cdn.district.in", ""), "tn_" + u.split("/")[-1]))

    # district-web chunks from homepage
    dst_srcs = ["https://cdn.district.in/district-web/_next/static/chunks/3b3bde0gznvut.js",
                "https://cdn.district.in/district-web/_next/static/chunks/1vrkrzsy-sjfe.js",
                "https://cdn.district.in/district-web/_next/static/chunks/0-38z7dzgcxbi.js",
                "https://cdn.district.in/district-web/_next/static/chunks/turbopack-32ju1ft_b1y9p.js",
                "https://cdn.district.in/district-web/_next/static/chunks/0sspni1_3waok.js",
                "https://cdn.district.in/district-web/_next/static/chunks/27ozuboy-mg1z.js",
                "https://cdn.district.in/district-web/_next/static/chunks/2t5m6l255zvhn.js",
                "https://cdn.district.in/district-web/_next/static/chunks/3-r9nnorulo0c.js",
                "https://cdn.district.in/district-web/_next/static/chunks/0nc0aniy-e165.js",
                "https://cdn.district.in/district-web/_next/static/chunks/3admm2jbe1jq6.js",
                "https://cdn.district.in/district-web/_next/static/chunks/0bfvvgfkk1yk9.js",
                "https://cdn.district.in/district-web/_next/static/chunks/13dcswqt3ni5k.js",
                "https://cdn.district.in/district-web/_next/static/chunks/3f6vvan9pcth8.js",
                "https://cdn.district.in/district-web/_next/static/chunks/2j_59m72ho85y.js",
                "https://cdn.district.in/district-web/_next/static/chunks/3aiqvvd_foi6y.js"]
    for u in dst_srcs:
        jobs.append(("cdn.district.in", u.replace("https://cdn.district.in", ""), "ds_" + u.split("/")[-1]))

    ok = 0
    for h, p, tag in jobs:
        fn = os.path.join(OUT, tag)
        if os.path.exists(fn) and os.path.getsize(fn) > 1000:
            ok += 1
            continue
        try:
            st, raw = get(h, p)
            if st == 200:
                open(fn, "wb").write(raw)
                ok += 1
                print("saved %s (%d KB)" % (tag, len(raw) // 1024), flush=True)
            else:
                print("fail %s [%d]" % (tag, st), flush=True)
        except Exception as e:
            print("exc %s %s" % (tag, repr(e)[:80]), flush=True)
    print("downloaded %d/%d" % (ok, len(jobs)), flush=True)


if __name__ == "__main__":
    main()
