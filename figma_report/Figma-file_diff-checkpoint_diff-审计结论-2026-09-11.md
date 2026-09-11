# Figma file_diff/checkpoint_diff 面 SQLi 全格结论（r198→r208，2026-09-11）

> 面：`POST /api/file_diff/v2/checkpoint_diff/{file_key}`（唯一存活版本；v1/v3/无版本段全 404）
> 身份：A `1666382703778278399`（starter）；B cookie 09-02 版已失效（401，双身份对照存缺口）
> 结论：**全参数 × 全注入形态零差分、零时延；端点对所有可达合法组合稳定 500（业务层 diff 引擎）
> → 无公开可利用 SQL 注入行为。**

---

## 一、端点语义（JS 实证 · figma_app-main.js @2587384）

调用链（版本历史"对比" UI）：
1. `et(versionId, store)` → `ee(id, versionHistory)` 从版本列表找版本对象
2. → `Q(n.id, store)` → **`J(openFile.key, 版本id, store.fileVersion, nodesToDiff?)`**
3. J 内构造 URLSearchParams 后 `axios.post("/api/file_diff/v2/checkpoint_diff/${fileKey}", void 0, {params})`

| 参数 | 语义 | 备注 |
|---|---|---|
| diff_version | 前端常量 `N.C2()` | 实测有效域 1-5；0/-1/10→400 "Invalid diff version" |
| from_file_version_id | 历史版本 id（UI 点选） | **真名=snake_case**（错误文案写驼峰是误导） |
| migration_version | 编辑器 `store.fileVersion`（autosave 号） | 完全不校验（abc/-1/100 全进业务） |
| nodes_to_diff | 逗号分隔节点（可选） | UI 真实调用不传；单独传无行为差分 |
| direction | 与 ffv **xor 互斥** | versions API 分页语义；direction 形态→404 unparseable |

- 成功判定：响应含 `meta.checkpoint_diff.signed_url`；失败文案 "Error viewing what's changed between file versions."；成功后 `crossOriginGetAny(signed_url)` 拉 diff 二进制。
- 客户端头构造（935 chunk @773209）：`Accept` / `Content-Type` / **`X-Csrf-Bypass:"yes"`** / `extraDefaultHeaders{tsid, X-Figma-User-Plan-Max}` / **`X-Figma-Client-Version`=release_manifest_git_commit** / `X-Figma-User-ID`。

## 二、校验链（层序 + 指纹）

| 序 | 层 | 触发输入 → 响应 |
|---|---|---|
| 0 | 路由/方法 | 非 POST→405（`Allow: OPTIONS, POST`）；v1/v3/无版本段→404；空 fk→404 page not found |
| 1 | fk 网关 | 非法 fk（带引号/注入串/随机 25 字符/版本 id）→ **403** "You don't have permission to view this file."（全形态单态 零分叉） |
| 2 | schema | `diff_version` 非数字→**400** "'diff_version' must be a valid number, received type String" |
| 3 | xor/缺参 | direction+ffv 同给或全缺→400（r198 首轮） |
| 4 | ffv↔fk 关联 | ffv 不属于该文件→**404** "Not found."（`0 OR 1=1`→前缀解析 0→查无） |
| 5 | 业务层 | 全合法组合→**500** "Error updating diff." |

## 三、注入面矩阵（全负）

| 槽位 | 构造 | 响应 | 判读 |
|---|---|---|---|
| diff_version | `1'` / `2 AND 1=1` | 400 类型拒（zod number） | 强校验，闭 |
| from_file_version_id | `<id>'` / `<id>'--` / `<id>' AND '1'='1` / `<id>' AND '1'='2` | 全 500 同响应 | to_i 前缀解析吸收语法尾部，**布尔对零分叉** |
| from_file_version_id | `0 OR 1=1` / `0 OR 1=2` | 双双 404 同构 | 解析为 0→关联门查无 |
| from_file_version_id | `;SELECT pg_sleep(3)--` / `'||pg_sleep(3)||'` | 500，579-1257ms | **无时延**，非 SQL 执行 |
| migration_version | `'` `'--` `AND 1=1/1=2` `;SELECT pg_sleep` `'||pg_sleep||'` | 全 500 同响应 | 无信号（不校验也不进语法） |
| nodes_to_diff | `0:1` / `0:1'` / `0:1' AND '1'='1` | 全 500 同响应 | 无信号 |
| HPP/数组 | ffv 重复 / ffv[] / 有效+注入混合 | 全 500 同响应 | 无信号 |
| fk（path） | `'` `'--` `' AND 1=1/1=2` `;SELECT pg_sleep` `'||pg_sleep||'` `' OR '1'='1` | 统一 403 零分叉 | 网关先于一切，**无时延** |
| 时间维终审 | 基线 965/1561/1942ms vs 全部 sleep 探针 579-1257ms | 全重叠 | 无慢=无 SQL 执行 |

## 四、500 归因（三维排除）

1. **形态维（r204）**：从 JS 挖出全客户端头（X-Csrf-Bypass:yes / tsid / X-Figma-Client-Version=真值 `1396308eb98e74bf4f7c72c27e72fc0d1e952816` / X-Figma-User-Plan-Max:starter）全量补齐 + 逐头减法对照 → 500 不变 ⇒ "请求不像官方客户端"假设排除。
2. **数据维**：单版本（LnVEzMlZ，版本 disabled:true）/ 多版本（M 6 版本，file_multiplayer+file_savepoint 正常）/ 跨身份文件（A 读 B 的文件 M）→ 500 恒在。
3. **时间维**：pg_sleep 探针全快 ⇒ 稳定业务层错误，非注入所致。

**归属**：业务层 diff 引擎对所有可达组合稳定失败（源站缺陷/服务故障）；`X-Cache: Error from cloudfront` + `Via: *.cloudfront.net` = CloudFront 对源站 5xx 的透传标记（非 CDN 自身错误）。

## 五、边界与缺口

- 未做真实浏览器 UI 抓包（环境限制）——如有浏览器环境，UI 点"版本对比"实抓为最终对照。
- B 身份 401 未完成双身份对照；A 对 B 的文件 M 版本列表可读（200），diff 打点同 500。
- mv 真值（store.fileVersion）外部不可观测，但 r203 证 mv 全不校验、任何值同响应，不影响结论。
- admin 面板路径 `/api/admin/checkpoint_diffs/{e}`、`/api/admin/figmascope_checkpoint_diffs/{e}` 对普通账号 404（路由级屏蔽）。

## 六、资产

- 探针脚本：`_figma_r198_fdiff_base.py` ~ `_figma_r208_admin.py`（11 个）
- JS 挖掘：`_tmp_fd_ctx2.py` ~ `_tmp_fd_ctx13.py`
- 输出：`_r198_*` ~ `_r208_*`（80+ 文件）；`_r204_filepage.html`（文件页快照 902KB，含 manifest 真值）

## 七、沉淀（已回流 CHANGELOG 2026-09-11）

- 06-送达与过障：`D4 请求形态复刻排除法`
- 03-判读库：CloudFront 边缘头指纹行 / 数字位前缀解析行 / 500 归因第三维（形态维）
- 05-实战案例：案例 9
- 01-入参矩阵：V2 关联 id 型数字位
