# Figma admin_requests 面 SQLi 全格结论（r196ai→an，2026-09-10）

> 面：`/api/plans/:plan_id/admin_requests*`（3 个 GET 端点）
> 账号：PLAN1 `cc6b6125-a07f-4d39-a54c-50ef65f33919`（free，本面 0 条数据 → 数据面死，判据=错误行为+时延+状态差分）
> 结论：**16 个参数全格打满，15 个白名单/参数化封死，1 个（cursor）为 opaque token 不可构造。无 SQLi 证据。**

## 一、JS 解密（figma_app-main.js @2719500-2728000）

1. **request_types[] 真值**（大写常量名→小写真值）：
   `{ACCOUNT_TYPE_REQUEST:"account_type_request", AI_CREDIT_REQUEST:"ai_credit_request", OAUTH_APP_REQUEST:"oauth_app_request"}`
   ——AH 波全 400 的根因：打的是大写常量名（值域找错）。
2. **counts 参数名**：`toQueryParameters({queryString, requestPermissionLevel, viewAll})` 经 `c.A()` 转 **snake_case** 发送：`query_string` / `request_permission_level` / `view_all`。
   ——AH13-15 打 camelCase 全静默 200 = **参数名错被忽略**（非参数化安全）。
3. **双解析路径**：裸名 `request_types` 走 route typecheck（JSON 数组文本）；`request_types[]` 走数组收集（Rails 强参数）。
4. **服务端=Rails**：强参数错误 `Invalid query parameters: expected Array (got String) for param 'request_types'`。
5. **cursor**：客户端纯透传（无解码逻辑）；服务端 base64+JSON 消费。

## 二、逐参数判定（对账核心）

| # | 参数 | 端点 | 槽位 | 打过的构造 | 判定 |
|---|---|---|---|---|---|
| 1 | request_types[] | dv/list | V6 集合 | 大小写/尾空格/NUL/注入元素/合法+注入混合/嵌套hash/嵌套数组/多值/[0]下标/裸名混发/非法在前 | **精确白名单{3小写值}**，全拒（错误回显原值），死 |
| 2 | request_types(裸名) | dv | A 结构 | `["account_type_request"]` / 含注入 / 混发 | typecheck JSON 层 400（`Expected: '['`），死 |
| 3 | query_string | dv/list | V1/V5 | `'` / `' OR '1'='1` / `%` / `_` / `x' AND '1'='2` / pg_sleep 时延 / 堆叠 / 3000字符 | **全静默 200 + 零时延**（0.6-0.68s）= 参数化/未生效，死 |
| 4 | query_string | counts | V1/V5 | 同上（snake_case 名验证） | 同上，死 |
| 5 | sort_order | list | I3 | `desc'` | 白名单 `must be 'asc' or 'desc'`，死 |
| 6 | view_all | list/counts | V4 | `true'` / 数组 | 白名单 `must be 'true' or 'false'`，死 |
| 7 | billing_group_ids[] | list | V6/V2 | 1 / 2-1 / 1.0 / -1 / 01 / int64溢出 / +1 / 全角 / 前导空格 / `1'` / `1 AND 1=1` | **`\d+` 正则**（前导零/溢出宽容，其余全拒），死 |
| 8 | request_seat_types[] | list | V6 | collaborator / `collaborator'` / `' OR '1'='1` | 白名单，死 |
| 9 | requester_permission_levels[] | list | V6 | admin / `admin'` / `' OR '1'='1` | 白名单，死 |
| 10 | request_permission_level | counts | 枚举位 | guest/member/owner/admin/OWNER/ADMIN/all/everyone/Guest/尾空格/`guest'`/`member'`/注入 | **精确白名单{guest,member}**（无 trim），死 |
| 11 | cursor | list | token 位 | **54+ 结构探针**（见三节） | **opaque token，外部不可构造**，无证据 |
| 12-16 | 端点级 | - | - | planId 越权对照（W5/W6：403 权限门正确） | 死 |

## 三、cursor 深挖全过程（AI-AN 六轮，唯一异常点）

**行为谱**（oracle=状态码+server-timing）：

| 输入（base64 解码后） | 结果 | 判读 |
|---|---|---|
| 非 base64（`abc`）/ 非 JSON（`{}` 原文） | 200 | decode64 宽容 → JSON.parse 抛错 → **rescue 忽略** |
| `null` | 200 | 显式 nil 特判 |
| **101+ 层嵌套**（120层→200；80层→500） | 200 | **JSON::NestingError 被 rescue**（Ruby max_nesting=100 吻合） |
| `{}` / `[]` / `"1"` / 28 单字段 / 组合 / 元组`["1"]` / `__requestId` / 命名变体 / `{"v":1}` | **500** | 解析成功且非 nil → 进处理链 → **浅层崩** |

**判读要点**：
- 通用 500（`Internal server error`）无任何细节泄露；**app;dur 124-385ms 与 200/400 同量级** → 崩点极浅（未到 DB 查询）。
- 收口判定：**服务端生成的 opaqued token**（结构含未知早检查，可能 version/signature），**外部结构化构造 54+ 发零差异化 → 注入路径不可达**。
- 副产品：cursor 对任意"合法 JSON 非 null"输入触发未处理异常（500）——低价值记录，不足以成报告。

## 四、通道覆盖对账（06-送达与过障）

| 通道族 | 本面覆盖 |
|---|---|
| A 结构语法 | `[]` 数组后缀 / 裸名 / `[0]` 下标 / 混发（HPP）/ JSON 数组文本 —— 全打 |
| B 编码族 | NUL 截断 / 尾空格 / 前导空格 / 大小写 / Unicode 数字 / `+`号 —— 全打 |
| C 类型混淆 | 嵌套 hash/数组元素 / 类型变体(null/数字/字符串) / 参数名映射(camel↔snake 双向验证) —— 全打 |
| D 组合策略 | pg_sleep 时延(3端点) / 堆叠 / 3000 字符超长 / 深度嵌套 —— 全打 |

## 五、本面资产（脚本）

- `_figma_r196ai_adminreq2.py`（判别面+18发注入）
- `_figma_r196aj_hpp.py`（双路径+枚举+时延+数字位）
- `_figma_r196ak_cursor.py`（cursor 形态差分+类型混淆）
- `_figma_r196al_cursor2.py`（28 单字段+X-Runtime oracle+深嵌套）
- `_figma_r196am_cursor3.py`（深度临界+元组+命名变体）
- `_figma_r196an_cursor4.py`（v/version 收口验证）
- 输出：`_r196ai_*.txt` ~ `_r196an_*.txt`（共 80+ 文件）

## 六、沉淀到经验库（已回流，见 CHANGELOG）

1. **Rails 强参数指纹** → 03
2. **`[]`/裸名/下标 三形态双路径** → 06 A 族
3. **序列化名转换陷阱（camelCase 静默忽略）** → 06 C 族（*重要：静默 200 的第一嫌疑是"参数名没被识别"而非"参数化安全"*）
4. **opaque cursor 的 oracle 方法论**（base64+JSON / max_nesting rescue / 通用 500 浅层崩判读 / server-timing 头）→ 06 D 族 + 03
5. **枚举位"精确匹配"证据链**（尾空格/NUL 拒 vs trim 放行的分野）→ 03
6. **数字位 `\d+` 规则**（前导零/溢出宽容）→ 01 V2
