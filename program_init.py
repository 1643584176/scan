#!/usr/bin/env python3
"""HackerOne 赏金项目初始化脚本:抓取平台规则与 scope,生成规范化的测试依据文件。

每次切换测试目标时先运行本脚本(或调用 program-init skill),确保测试严格在
规则与 scope 内进行。

用法:
  python program_init.py wolt                          # 初始化 HackerOne 项目(用户名固定 pccp)
  python program_init.py --list                        # 列出已初始化的项目

输出(programs/<name>/ 目录):
  raw_policy.txt   规则页面原始文本
  raw_scope.txt    scope 页面原始文本
  config.json      结构化配置:scope / out of scope / 测试账号 / 交战规则 / 赏金
  PROGRAM.md       整理后的可读文档
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

BASE_DIR = Path(__file__).resolve().parent
PROGRAMS_DIR = BASE_DIR / "programs"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# 测试账号 id,如 user_id is 670fa3e9ead6e49d65cc3614
TEST_ID_RE = re.compile(r"\b(user|venue|account|page|slug)[_ ]?id\b[^\n]{0,60}", re.I)
# 金额,如 $150 / €3,500 / 1,500
MONEY_RE = re.compile(r"[$€£]\s?[\d][\d,]*", re.I)
# 速率限制,如 max. 3 requests/sec
RATE_RE = re.compile(r"max\.?\s*\d+\s*(?:req(?:uest)?s?|requests?)\s*/\s*(?:sec|second|s)", re.I)
# 请求头,如 X-HackerOne-Research: [H1 username]
HEADER_RE = re.compile(r"X-HackerOne-Research[^\n]{0,80}", re.I)
# 测试实体 URL(如 test venue)
TEST_URL_RE = re.compile(r"https?://[^\s\"']+(?:test|Test)[^\s\"']*", re.I)


def _print(msg: str) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print(msg)


def _fetch_text(url: str, click_selector: str | None = None, wait_ms: int = 12000):
    """用 playwright 打开 URL,可选点击客户端路由链接,返回 (title, body_text)。"""
    if sync_playwright is None:
        raise RuntimeError("未安装 playwright,请先执行: pip install playwright")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        try:
            page = browser.new_page(user_agent=UA)
            page.goto(url, timeout=90000, wait_until="domcontentloaded")
            page.wait_for_timeout(wait_ms)
            if click_selector:
                try:
                    page.click(click_selector, timeout=10000)
                    page.wait_for_timeout(wait_ms)
                except Exception:
                    _print(f"  [warn] 点击 {click_selector} 失败,仅抓取当前页")
            title = page.title()
            text = page.inner_text("body")
            page.close()
            return title, text
        finally:
            browser.close()


def _is_not_found(title: str, text: str) -> bool:
    return "page not found" in title.lower() or "this page can't be found" in text.lower()


def fetch_hackerone(program: str):
    """抓取 HackerOne 项目的 policy 与 policy_scopes 页面。"""
    base = f"https://hackerone.com/{program}"
    _print(f"  [1/3] 打开规则页 {base}")
    title, policy_text = _fetch_text(base)
    if _is_not_found(title, policy_text):
        raise RuntimeError(f"项目不存在或无法访问: {base}")
    _print(f"  [2/3] 规则页已抓取 ({len(policy_text)} 字符)")

    scope_text = ""
    try:
        _print("  [3/3] 打开 Scope and Rewards 页")
        _, scope_text = _fetch_text(
            base, click_selector=f"a[href='/{program}/policy_scopes']"
        )
        _print(f"       scope 页已抓取 ({len(scope_text)} 字符)")
    except Exception as exc:
        _print(f"  [warn] scope 页抓取失败: {exc}")
    return policy_text, scope_text


# 资产名模式:域名(可带 *. 通配符)、逗号分隔多域名、URL
ASSET_NAME_RE = re.compile(
    r"^(?:\*\.)?(?:[a-z0-9-]+\.)+[a-z0-9-]+(?:,(?:[a-z0-9-]+\.)+[a-z0-9-]+)*$",
    re.I,
)
URL_ASSET_RE = re.compile(r"^https?://\S+$", re.I)
# 展开行中单独出现的类型行
KNOWN_TYPES = {"domain", "wildcard", "source code", "other", "ip range",
               "ios: app store", "android: play store", "code", "mobile"}
SKIP_SCOPE_WORDS = {
    "asset name", "coverage", "max. severity", "bounty", "last update",
    "resolved reports", "type", "search", "scope", "all scopes",
    "maximum severity", "bounty eligibility", "any", "all",
    "download burp suite project configuration file", "download csv",
    "view changes", "in scope", "excluded assets", "out of scope",
}
SEVERITIES = {"critical", "high", "medium", "low", "none"}


def parse_hackerone_scope(text: str) -> list[dict]:
    """从 policy_scopes 页面文本提取资产列表(按 In scope / Out of scope 分组)。

    HackerOne scope 页存在两种资产行格式:
      - 紧凑行: "<name>\t<Type>"(如 "www.valvesoftware.com\tDomain")
      - 展开行: "<name>\n说明文字\n\t<Type>\nIn scope"(名称/类型/分组分行)
    资产属性(严重度、赏金资格、日期、报告数)紧跟资产出现。
    """
    assets: list[dict] = []
    section = "Uncategorized"
    pending: dict | None = None  # 最近添加、属性尚未补全的资产
    date_re = re.compile(r"^\w{3}\s+\d{1,2},\s+\d{4}$")
    pager_count = 0  # 资产区有 "1-26 of 26" 分页行;第二次出现后是页脚区(公司信息/Stats),截断
    for raw in text.splitlines():
        low = raw.strip().lower()
        if not low:
            continue
        if re.fullmatch(r"\d+-\d+ of \d+", low):
            pager_count += 1
            if pager_count >= 2:
                break
            continue
        # 分组标题(同时补正紧邻资产的 section,展开行中分组在类型之后)
        if low in ("in scope", "out of scope", "excluded assets"):
            section = raw.strip()
            if pending is not None:
                pending["section"] = section
            continue
        if re.fullmatch(r"\$?[\d,]+", low):
            continue
        # 资产属性行
        if pending is not None:
            if low in SEVERITIES:
                pending["max_severity"] = low
                continue
            if low in ("eligible", "ineligible"):
                pending["bounty"] = low
                continue
            if date_re.match(low) or re.fullmatch(r"\d+\s*\(\d+%\)", low):
                continue
        if "\t" in raw:
            parts = [p.strip() for p in raw.split("\t") if p.strip()]
            if not parts:
                continue
            first = parts[0]
            first_low = first.lower()
            if len(parts) >= 2:
                # "<name>\t<Type>" 紧凑行;名称须为资产模式,或第二字段是已知类型
                # (覆盖 Steam Servers\tOther 这类带空格的资产名,排除统计行如 Total bounties paid\t$...)
                is_asset = (ASSET_NAME_RE.match(first) or URL_ASSET_RE.match(first)
                            or parts[1].lower() in KNOWN_TYPES)
                if is_asset and first_low not in SKIP_SCOPE_WORDS:
                    assets.append({"name": first, "type": parts[1], "section": section,
                                   "max_severity": "", "bounty": ""})
                    pending = assets[-1]
            elif ASSET_NAME_RE.match(first):
                # 名称后带 tab 尾巴的展开行首(类型在后续行)
                assets.append({"name": first, "type": "", "section": section,
                               "max_severity": "", "bounty": ""})
                pending = assets[-1]
            elif first_low in KNOWN_TYPES and pending is not None:
                # "\t<Type>\t" 类型行,补到最近资产
                pending["type"] = first
        else:
            if ASSET_NAME_RE.match(low) or URL_ASSET_RE.match(low):
                # 展开行的名称行;URL 资产(如 github.com/...)以展开行出现,
                # 公司信息 URL 在页脚区,已由分页符截断不会误抓
                assets.append({"name": low, "type": "", "section": section,
                               "max_severity": "", "bounty": ""})
                pending = assets[-1]
            elif low in SKIP_SCOPE_WORDS:
                continue
            # 其余为说明文字/统计行,忽略
    return assets


def parse_policy(text: str) -> dict:
    """从规则页文本提取交战规则、测试账号、out of scope 清单、报告要求。"""
    rules: dict = {
        "required_headers": [],
        "user_agent": "",
        "rate_limit": "",
        "test_accounts": [],
        "test_entities": [],
        "forbidden": [],
        "report_rules": [],
        "notes": [],
    }
    for m in HEADER_RE.finditer(text):
        hdr = m.group(0).replace("\n", " ").strip()
        if hdr not in rules["required_headers"]:
            rules["required_headers"].append(hdr)
    m = RATE_RE.search(text)
    if m:
        rules["rate_limit"] = m.group(0)

    # 测试账号 id
    seen_ids = set()
    for m in TEST_ID_RE.finditer(text):
        line = m.group(0).replace("\n", " ").strip().rstrip(".;,")
        if line not in seen_ids:
            seen_ids.add(line)
            rules["test_accounts"].append(line)
    # 测试实体 URL
    for m in TEST_URL_RE.finditer(text):
        url = m.group(0).rstrip(".,)")
        if url not in rules["test_entities"]:
            rules["test_entities"].append(url)

    # out of scope 清单:从 "Out of scope"/"Exclusions" 起收集,到下一主章节为止;
    # general/application/web/mobile 是子分类标题,跳过但继续收集条目
    OOT_START = {"out of scope", "exclusions", "scope exclusions"}
    OOT_END = {"overview", "in scope", "dependencies", "assessing severity and rewards",
               "responsible disclosure and guidelines", "the fine print",
               "program rules", "disclosure policy", "testing plan",
               "test entities", "where can we get credentials", "safe harbour",
               "safe harbor", "faq", "legacy hall of fame", "top hackers",
               "thanks", "rewards summary", "program highlights", "scope"}
    lines = text.splitlines()
    in_oot = False
    for line in lines:
        low = line.strip().lower()
        if low in OOT_START:
            in_oot = True
            continue
        if in_oot and low in OOT_END:
            in_oot = False  # 一个项目可能有多段 exclusions(如 Scope exclusions + Exclusions)
            continue
        if in_oot and low in ("general", "application", "web", "mobile", "i"):
            continue
        if in_oot and line.strip():
            item = line.strip()
            if item not in rules["forbidden"] and item not in ("Learn more",):
                rules["forbidden"].append(item)

    # 报告要求
    for line in lines:
        low = line.strip().lower()
        if re.search(r"(detailed reports|reproducible steps|keep report|words per report|"
                     r"one vulnerability per report|brief and concise|must be demonstrated|"
                     r"report must meet|good faith effort|let us know as soon as possible)", low):
            rules["report_rules"].append(line.strip())

    # 关键约束备注(常见于具体项目规则)
    note_patterns = [
        r"subdomains?\s+of\s+(?:the\s+)?listed\s+websites[^.\n]*",
        r"cookie called ['\"]?sessionid[^.\n]*\.?",
    ]
    for pat in note_patterns:
        for m in re.finditer(pat, text, re.I):
            note = m.group(0).replace("\n", " ").strip()
            if note not in rules["notes"]:
                rules["notes"].append(note)
    return rules


def extract_bounties(text: str) -> list[str]:
    amounts = []
    for m in MONEY_RE.finditer(text):
        val = m.group(0)
        if val not in amounts:
            amounts.append(val)
    return amounts


def build_config(program: str, username: str, policy_text: str, scope_text: str) -> dict:
    assets = parse_hackerone_scope(scope_text)
    rules = parse_policy(policy_text)
    # 赏金表在 scope 页(如 "Low $150 Medium $750 ...");"$1 - $5,000 / <$10,000" 是程序统计,
    # >$100k 的(如总赏金/90天统计)也不是赏金表,统一过滤掉
    def _money_value(s: str) -> float:
        try:
            return float(s.replace("$", "").replace("€", "").replace("£", "").replace(",", ""))
        except ValueError:
            return 0.0

    bounties = [b for b in extract_bounties(scope_text)
                if b not in ("$1", "$10,000") and _money_value(b) <= 100000]
    # scope 页面的 Out of scope 分组归入 forbidden
    if assets:
        rules["forbidden"].extend(
            a["name"] for a in assets if a["section"] == "Out of scope"
        )
    in_scope = [
        {"name": a["name"], "type": a["type"],
         "max_severity": a["max_severity"], "bounty": a["bounty"]}
        for a in assets
        if a["section"] in ("In scope", "Excluded Assets")
    ]
    out_of_scope_domains = [
        {"name": a["name"], "type": a["type"],
         "max_severity": a["max_severity"], "bounty": a["bounty"]}
        for a in assets
        if a["section"] == "Out of scope"
    ]
    return {
        "name": program,
        "platform": "hackerone",
        "program_url": f"https://hackerone.com/{program}",
        "username": username or "your_hackerone_username",
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bounties": bounties,
        "scope": {
            "in_scope": in_scope,
            "out_of_scope_domains": out_of_scope_domains,
            "count": len(in_scope),
        },
        "rules": rules,
    }


def render_markdown(cfg: dict, raw_files: dict) -> str:
    lines = [
        f"# {cfg['name']} - 漏洞赏金项目初始化报告",
        "",
        f"- 平台: {cfg['platform']}",
        f"- 页面: {cfg['program_url']}",
        f"- 抓取时间: {cfg['fetched_at']}",
        f"- 测试用户名: {cfg['username']}(用于规则请求头)",
        "",
        "## Scope",
    ]
    in_scope = cfg["scope"]["in_scope"]
    if in_scope:
        lines.append("| 资产 | 类型 | 最高严重度 | 赏金资格 |")
        lines.append("|---|---|---|---|")
        for a in in_scope:
            lines.append(f"| {a['name']} | {a['type']} | {a['max_severity']} | {a['bounty']} |")
    else:
        lines.append("_(scope 解析见 raw_scope.txt / raw_policy.txt)_")
    lines.append("")
    if cfg["scope"]["out_of_scope_domains"]:
        lines.append("## Out of scope 域名")
        for a in cfg["scope"]["out_of_scope_domains"]:
            lines.append(f"- {a['name']}({a['type']})")
        lines.append("")
    if cfg["bounties"]:
        lines.append("## 赏金(从页面提取,含统计值,以规则页为准)")
        lines.append("、".join(cfg["bounties"]))
        lines.append("")
    rules = cfg["rules"]
    if rules["required_headers"]:
        lines.append("## 必须携带的请求头")
        lines.extend(f"- `{h}`" for h in rules["required_headers"])
        lines.append("")
    if rules["user_agent"]:
        lines.append(f"- User-Agent: `{rules['user_agent']}`")
    if rules["rate_limit"]:
        lines.append(f"- 限速: `{rules['rate_limit']}`")
    if rules["notes"]:
        lines.append("## 关键约束备注")
        lines.extend(f"- {n}" for n in rules["notes"])
        lines.append("")
    if rules["test_accounts"]:
        lines.append("## 测试账号/实体")
        lines.extend(f"- {a}" for a in rules["test_accounts"])
        lines.append("")
    if rules["test_entities"]:
        lines.extend(f"- {u}" for u in rules["test_entities"])
        lines.append("")
    if rules["report_rules"]:
        lines.append("## 报告要求")
        lines.extend(f"- {r}" for r in rules["report_rules"])
        lines.append("")
    if rules["forbidden"]:
        lines.append("## Out of scope 测试类型(规则禁测)")
        lines.extend(f"- {f}" for f in rules["forbidden"][:60])
        lines.append("")
    lines.append("## 原始抓取文件")
    for label, path in raw_files.items():
        lines.append(f"- {label}: `{path}`")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化 HackerOne 赏金项目:抓规则与 scope")
    parser.add_argument("program", nargs="?", help="项目名/handle,如 wolt")
    parser.add_argument("--username", default="pccp",
                        help="HackerOne 用户名(默认固定 pccp,一般不用传)")
    parser.add_argument("--list", action="store_true", help="列出已初始化的项目")
    args = parser.parse_args()

    if args.list:
        if not PROGRAMS_DIR.exists():
            _print("还没有初始化过任何项目")
            return
        for cfg_file in sorted(PROGRAMS_DIR.glob("*/config.json")):
            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
            _print(f"- {cfg['name']:20s} {cfg['platform']:10s} {cfg['fetched_at']}")
        return

    if not args.program:
        parser.error("需要提供项目名(或使用 --list)")

    name = args.program.lower()
    out_dir = PROGRAMS_DIR / name
    out_dir.mkdir(parents=True, exist_ok=True)

    policy_text, scope_text = fetch_hackerone(name)
    cfg = build_config(name, args.username or "pccp", policy_text, scope_text)

    raw_files = {"规则页": out_dir / "raw_policy.txt"}
    (out_dir / "raw_policy.txt").write_text(policy_text, encoding="utf-8")
    if scope_text:
        (out_dir / "raw_scope.txt").write_text(scope_text, encoding="utf-8")
        raw_files["Scope页"] = out_dir / "raw_scope.txt"

    (out_dir / "config.json").write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "PROGRAM.md").write_text(
        render_markdown(cfg, raw_files), encoding="utf-8"
    )

    _print(f"\n初始化完成: {out_dir}")
    _print(f"  规则页文本   : {len(policy_text)} 字符")
    if scope_text:
        _print(f"  scope 页文本 : {len(scope_text)} 字符")
        _print(f"  解析出资产   : {cfg['scope']['count']} 个 in-scope 资产")
    _print(f"  输出文件     : config.json / PROGRAM.md")


if __name__ == "__main__":
    main()
