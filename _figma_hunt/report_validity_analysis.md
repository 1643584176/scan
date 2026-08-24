# 已提交报告有效性复测分析（2026-08-24）

## 背景
- 报告1: H1-private-make-source-code-authz-chain (HIGH, 8-18 提交)
  - FileMakeVersionsView 匿名可枚举私有 Make 版本(chatThreadId+codeSnapshotKey)
  - GET /api/rev/{fk}/code_snapshot/{key} 任意登录用户可下载完整源码
- 报告2: H1-published-package-missing-authz (MEDIUM, 8-18 提交)
  - POST/DELETE /api/files/{fk}/published_package 任意登录用户可增删包

## 复测方法（8-24, A/B cookie 均有效）
- 文件当前状态: 5zb5YkoxMa09KpqOyuLcHD 已私有(link_access=inherit)
- 纯净 B cookie 构造成功(/api/user 200, threads 403 正常)
- 匿名 WS + 纯净B WS + A owner WS 三组对照

## 复测结果

### 报告1 相关
| 测试 | 匿名 | 纯净B | A owner |
|---|---|---|---|
| /api/files/{fk} metadata | 403 | 403 | 200 |
| /api/versions/{fk} | 403 | 403 | 200 |
| FileMakeVersionsView (WS) | 空壳 initial={} | 空壳 initial={} | 空壳 initial={} |
| make_versions REST | 401 | 403 | 200 但空列表 |
| code_snapshot fake-key | 401 | - | 404 "Code snapshot not found" |

- 当前文件无任何 MakeVersion 数据基线(版本在私有化/清理时被删)
- 匿名/纯净B 均返回空壳 → **无法复现泄露**

### 报告2 相关
- POST published_package: A owner 401 / 原始污染B 401 / 纯净B 401 / 带UID头 401 / 纯A-token 401
- livegraph publishedPackages: A owner 订阅空壳
- **所有身份全部 401 missing_authentication → 端点当前不可写，无法复现**

## 提交时证据缺陷（从工作区文件还原）

### 报告1 的严重疑点
1. **测试文件当时是公开的**: _lg_public_make_threads.py (8-18 09:28, 提交前7h) 注释明确
   "owner-controlled public Figma Make file"; 8-19 的 _make_privatize_probe/_make_privatize2
   才尝试将其私有化 → 报告写 "private Figma Make file" 与事实不符
2. **角色颠倒**: 报告声称 victim=B/attacker=A, 但实际测试文件 5zb5YkoxMa09KpqOyuLcHD
   creator_id=A(1666382703778278399), 攻击脚本用 B cookie ( _lg_make_views.py )
3. **匿名 WS 声称无脚本证据**: 唯一含 FileMakeVersionsView 的脚本带 B cookie 非匿名
4. **8-17~8-18 的 B cookie 污染状态未知**(ws_cookie_B_new.txt 8-18 17:13 已含 A+B 双 token,
   之前的版本被覆盖; 污染何时产生无法回溯)
5. 公开文件时代"匿名/登录用户拿到版本"可能只是公开可见性(公开文件版本历史本就可见) →
   与 PlanByFileKey 同类的公开性检查失败风险

### 报告2 的疑点
1. 8-17 唯一落盘 log (pkg_owner_delete_probe.log 18:35) 显示**全部 401**
   (B create 401 / A create 401), 声称成功的输出未落盘
2. 8-17 的 B cookie 污染状态未知; 若当时含 A token, "B 删除 A 的包"可能是
   多账号 token 回退假象(identity-claim 同款机制)
3. 当前所有身份 401 → 疑似端点已被修复或当时测试依赖未记录条件

## 判定
- **报告1 (HIGH)**: 有效性存疑, "私有文件泄露"从未被严格证实(当时文件公开),
  当前无法复现; 报告描述(角色/私有性/匿名路径)与落盘证据多处矛盾
- **报告2 (MEDIUM)**: 当前无法复现(全身份 401); 若 8-17 确实成功过, 疑似已修复;
  污染 cookie 假象未排除

## 建议(供用户决策)
- 报告1: 高风险报告, 建议用户核对 triage 前是否主动撤回/补充说明
  (公开文件测试不能支撑 HIGH 私有文件泄露)
- 报告2: 复现失败, 若 triage 复测将同样失败; 等 triage 结果或主动撤回
- 后续测试必须遵守: 测试文件私有化确认 + 纯净 cookie + 落盘所有请求/响应
