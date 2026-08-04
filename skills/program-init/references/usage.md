# program_init.py 使用说明

HackerOne 赏金项目初始化脚本,位于 `D:\scan\program_init.py`。

## 命令

```bash
# 初始化项目(抓规则页 + scope 页;用户名固定 pccp,不需要传)
python program_init.py <handle>

# 列出已初始化的项目
python program_init.py --list
```

参数:
- `<handle>`:HackerOne 项目名,如 `wolt`
- `--username`:HackerOne 用户名,默认固定为 `pccp`,一般不用传

## 输出(programs/<handle>/)

| 文件 | 内容 |
| --- | --- |
| `raw_policy.txt` | 规则页(政策)原始文本 |
| `raw_scope.txt` | Scope and Rewards 页原始文本 |
| `config.json` | 结构化配置,测试的唯一依据 |
| `PROGRAM.md` | 整理后的可读文档 |

## config.json 关键字段

- `scope.in_scope` —— 允许测试的资产(域名 + tier),只测这些
- `scope.out_of_scope_domains` —— 明确排除的域名,不测
- `rules.required_headers` —— 请求必须带的头(如 `X-HackerOne-Research: [H1 username]`),缺了可能失去赏金资格
- `rules.test_accounts` / `rules.test_entities` —— 规则允许使用的测试账号/实体,不用真实用户数据
- `rules.forbidden` —— 禁测清单(资产类型 + 测试手段),逐一核对
- `rules.report_requirements` —— 报告要求
- `bounties` —— 各等级赏金,用于评估漏洞价值

## 技术要点(维护脚本时注意)

- HackerOne 政策页是 JS 渲染,必须用 Playwright 真实浏览器;静态请求拿不到内容
- Chrome 已有实例运行时 `channel="chrome"` 会报 EACCES,使用 `channel="msedge"`
- scope 页是客户端路由:直接访问 `/{handle}/policy_scopes` 会 404,需先打开 `/{handle}` 再点击 `a[href='/{handle}/policy_scopes']`(role 是 treeitem 不是 link)
- 输出含中文/`\xa0`,打印时需 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`,写文件用 `encoding="utf-8"`
- 页面加载需等待:进入规则页等 ~12s,点击导航后再等 ~12s
