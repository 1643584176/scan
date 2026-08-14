import sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    page = browser.new_page()
    page.goto("https://hackerone.com/figma/policy_scopes", timeout=45000)
    time.sleep(6)
    # 提取正文文本
    text = page.evaluate("document.body.innerText")
    open("h1_scope_text.txt", "w", encoding="utf-8").write(text)
    print(f"文本长度: {len(text)}")
    # 找 weave 相关段落
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if "weave" in ln.lower() or "weavy" in ln.lower():
            print(f"--- L{i}: {ln.strip()[:200]}")
    browser.close()
