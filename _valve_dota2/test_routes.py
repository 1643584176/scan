# -*- coding: utf-8 -*-
"""dota2 SPA 路由参数反射测试:渲染后检查 DOM 中 payload 出现位置"""
from playwright.sync_api import sync_playwright

PAYLOAD = "XVZPROBE9"
URLS = [
    ("newsentry-bad", "https://www.dota2.com/newsentry/" + PAYLOAD),
    ("newsentry-hex", "https://www.dota2.com/newsentry/0x" + PAYLOAD),
    ("dotaplustester", f"https://www.dota2.com/dotaplustester/{PAYLOAD}/{PAYLOAD}"),
    ("patches", "https://www.dota2.com/patches/" + PAYLOAD),
    ("templatepage", "https://www.dota2.com/templatepage?x=" + PAYLOAD),
    ("crownfall-q", "https://www.dota2.com/crownfall?x=" + PAYLOAD),
    ("search-q", "https://www.dota2.com/?q=" + PAYLOAD),
    ("lang-q", "https://www.dota2.com/home?l=" + PAYLOAD),
    ("patchnotes-q", "https://www.dota2.com/patchnotes/" + PAYLOAD),
    ("home-frag", "https://www.dota2.com/home#" + PAYLOAD),
]

with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True, args=["--no-proxy-server"])
    page = browser.new_page(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    for name, url in URLS:
        try:
            page.goto(url, timeout=45000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
            title = page.title()
            hits = page.evaluate("""(PAYLOAD) => {
                const res = [];
                const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
                let n;
                while (n = walker.nextNode()) {
                    if (n.children.length) continue;
                    const t = n.textContent || '';
                    if (t.includes(PAYLOAD)) res.push({tag: n.tagName, text: t.slice(0, 120)});
                    for (const attr of ['href','src','value']) {
                        const v = n.getAttribute(attr);
                        if (v && v.includes(PAYLOAD)) res.push({tag: n.tagName, attr, val: v.slice(0, 150)});
                    }
                }
                return res;
            }""", PAYLOAD)
            print(f"== {name} [{url}]")
            print(f"   title: {title[:120]!r}")
            if hits:
                for h in hits[:8]:
                    print(f"   HIT {h}")
            else:
                print("   no DOM reflection")
        except Exception as e:
            print(f"== {name} ERROR: {str(e)[:120]}")
    browser.close()
