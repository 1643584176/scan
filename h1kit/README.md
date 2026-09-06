# h1kit 使用说明(全局工具包)

把 H1 挖洞里**反复出现的纯代码操作**沉淀为可复用模块,放在 `F:\scan\h1kit\`。
运行任何脚本前先把工作目录切到 `F:\scan`(`cd F:/scan`),即可 `import h1kit`。

## 模块与 API

### 1. h1kit.gitbash —— Git Bash 陷阱规避(每次在终端跑 python 前看)

已反复踩过的坑:

| 坑 | 现象 | 规避 |
|---|---|---|
| 双引号被剥离 | `python -c "print(1)"` 语法错误 | 写 `.py` 文件,用 `python < 脚本.py`(stdin 方式) |
| 反引号被执行 | grep 模式里写 `` `order_by` `` → `command not found` | 用 `gitbash.pygrep()`(python 正则 grep) |
| `/tmp` 虚拟路径 | Windows python 打不开 `/tmp/x` | `gitbash.winpath('/tmp/x')` 转 `C:/Users/.../Temp/x` |
| `cd /tmp` 混用 | cwd 漂移、相对路径错乱 | 保持在 `F:\scan` 运行,脚本内用绝对 Windows 路径 |

常用:
```python
from h1kit import gitbash
gitbash.is_gitbash()                 # 当前是否在 git bash 下
gitbash.winpath('/tmp/h1.json')      # msys 路径 → Windows 路径
gitbash.py_run_cmd('x.py')           # 返回 'python < x.py'(推荐执行方式)
gitbash.pygrep(r'order_by', root, include=...)   # 带引号/反引号的安全 grep
gitbash.shell_memo()                 # 打印全部陷阱备忘
```

### 2. h1kit.h1data —— 找项目 / 查 scope(离线数据)

数据源:arkadiyt/bounty-targets-data(hackerone_data.json,缓存于 `h1kit/cache/`)。
注意:该 dump 只覆盖仓库跟踪的项目子集(约 450 个),用于**发现候选**;
完整政策全文必须由用户在 H1 页面提供(H1 政策页是 SPA,匿名抓取不可行,已验证多次)。

```python
from h1kit import h1data
h1data.update_dump(force=True)                      # 更新 dump(默认 1 天内不重复下载)
rows = h1data.find_programs(
    keywords=['search', 'api'],                     # 关键词(OR,匹配 name/url/资产)
    exclude=['figma', 'vercel'],                    # 排除已测项目(正则片段)
    bounty_only=True, state='open')
info = h1data.program_info('mongodb')               # 单项目详情(None = 不在 dump)
print(h1data.scope_assets('mongodb'))               # 打印 in/out-of-scope 资产
```

### 3. h1kit.net —— 网络状态诊断与低音量请求

```python
from h1kit import net
net.check_hosts(['app.box.com', 'api.github.com'])  # 并行 TCP 连通性(每主机 1 次握手)
net.probe_proxies()                                 # 探测本地/局域网代理 + 谷歌可达性 + 出口 IP
net.exit_ip()                                       # 当前出口 IP
st, hdrs, body = net.http_get('app.box.com', '/')   # 单次低音量 HTTPS GET
```

### 4. h1kit.scaffold —— 项目骨架与基线文档

```python
from h1kit import scaffold
d = scaffold.make_report_dir('mongodb')             # F:\scan\mongodb_report\{_js,_probes}
p = scaffold.make_baseline_md('mongodb', researcher='xxbo')  # 生成英文基线骨架
```

生成后:用户把 H1 政策全文粘贴进文档 → 填写 Hard Rules 检查清单 → 按
`skills/rule-baseline-first` 流程对照 → 才开始测试。

## 新增模块的规范

- 每个模块顶部写清:定位、使用场景、Usage 示例
- 新踩的坑(执行类)加进 `gitbash.py` 的陷阱表/`shell_memo()`
- 新爬取的重复数据源(如某平台 OpenAPI)缓存进 `h1kit/cache/` 并在 README 登记
- 缓存与凭据不入库:`.gitignore` 已含 `h1kit/cache/`
