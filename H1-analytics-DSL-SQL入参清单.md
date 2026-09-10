# HackerOne analytics DSL 注入测试入参清单（实际发送值）

> 2026-09-09 整理 — 供分析交接用。所有值均为实际发送过的字面量。

## 一、宽松 String 标识位置

### uid（query 级）

```
x/*（未闭合块注释）→ 正常执行(7)
```

（此前系列还测过: 单引号 / 双减号注释 / 换行 变体 → 全部无感正常执行）

### select.as / join as

```
cc' --
```

→ `RuntimeError: alias should match [A-Za-z][A-Za-z0-9_]`

### select.from

```
dim_hacker_reports        → 正常(数据仍主表, from 不覆盖来源)
dim_reports               → 正常(同主表数据)
j1                        → 正常(join 别名)
dim_reports' --           → RuntimeError: table 'dim_reports' --' not defined in schema
x                         → RuntimeError: table 'x' not defined in schema
```

### order_by.key

```
dim_hacker_reports__report_id       → 正常(倒序生效)
dim_hacker_reports__report_id DESC  → NoMethodError: undefined method '+' for nil
dim_hacker_reports__report_id, dim_hacker_reports__state → NoMethodError（同）
`report_id`（反引号）                → NoMethodError（同）
"report_id"（双引号标识符）          → NoMethodError（同）
report_id（列名简写）                → NoMethodError（同）
x / x' / 注释变体                    → NoMethodError（同）
```

### select.default

```
"0"       → 正常(7)
"+1"      → 正常(7)
"5"       → 正常(空组时返回 0, default 未达 SQL)
"x"       → GraphQL 层 Query execution error
"x'"      → 同
'x"'      → 同
"x\n-- y" → 同
"%s"      → 同
"1.5"     → 同
"1e3"     → 同
```

## 二、值位置（where right / in 数组元素）

### right.string（单值）

```
new' /*
```

→ 正常执行(0 行——值作纯字符串, bind 确认)

### right.strings（in 数组元素）

```
["new' --", "x"]  → 0（元素作纯字符串）
["new/*", "x"]    → 0（未闭合块注释无感）
["`new`", "x"]    → 0
["new"]           → 1（正对照）
```

## 三、谓词递归 or 列表（行为探测入参——非注入）

or 元素 = 完整谓词, 值变体: `new / duplicate / not-applicable / closed`（dim_hacker_reports state 分布: new=1, duplicate=1, not-applicable=5, closed=0）:

```
主条件 new + or[duplicate]                          → 2（单元素生效）
主条件 closed + or[duplicate]                       → 1（单元素生效）
主条件 new + or[duplicate 嵌套 or[not-applicable]]  → 7（嵌套递归生效）
主条件 new + or[duplicate, not-applicable]          → 1（多元素 or 被忽略）
主条件 closed + or[duplicate, not-applicable]       → 0（忽略）
主条件 closed + or[not-applicable, duplicate]       → 0（忽略, 反转同）
主条件 closed + or[new, new]                        → 1（重复元素去重后生效！）
主条件 closed + or[duplicate, duplicate]            → 1（同上）
主条件 closed + or[duplicate, duplicate, not-applicable] → 0
主条件 closed + or[duplicate, not-applicable, duplicate] → 0（乱序同）
主条件 closed + or[new, new, not-applicable]        → 0
主条件 closed + or 三元素[new, duplicate, not-applicable] → 0
主条件 new + or[]（空列表）                         → 1（空 or 正常）
```

**结论**: or 列表先 uniq（键 = 完整谓词），去重后 >1 元素 → 整个 or 静默丢弃（只主条件生效）；单元素/嵌套正常。过滤过度方向，无越权。

## 四、数字/边界位置

```
limit: -1  → "Query limit has to be between 1 and 5000"
offset: -1 → "Query offset cannot be negative"
```

## 五、having / 函数参数（结构残废判别）

**having**（operator: and/or + predicates[left: {field, function: count}, function: gt, right: {string}]）→ `NoMethodError: undefined method 'ref' for an instance of AnalyticsSelectInputType`

**select.function_with_args**（date_add）: `arguments: [{ string: "7 day" }]` → 返回原值（死参数不生效）

**where function_with_args**: date_add 间隔 `"7 day"` → 死参数（同）

## 六、benchmark 入口（第二翻译器）

**三参数**（benchmark_name/metric/aggregation_func）: 注入变体 → 恒 `error_types: ["AUTHORIZATION"]`

**interval**: `"year"` → GraphQL 层 Query execution error（唯一异常——值域非法未捕获）；`"week"/"day"/"month"/"quarter"`/空/注入变体 → 恒 AUTHORIZATION

**where/variables**: `\u0000` 探针 → 恒 AUTHORIZATION

## 七、跨表/计数判别基线（对照用）

- dim_reports / gateway_httpstream 等含 user 表: 任意 where 恒真/多条件/join/or → count 恒 0；sum → null；原始值 select → 空数组
- dim_hacker_reports（7 行自己的报告）: 原始值/聚合/分页/排序全正常
- 原始值 SELECT 形态（select 无 function）: `[{ field: dim_hacker_reports__report_id }]` → 7 行真实值
- 行级过滤在原始值模式/join 子查询/or 全生效（0 行表任意形态 = 0）

## 八、变量引用链与 right 值类型面（DJ 系列补充）

**AnalyticsComplexInputType 全字段**（left/right 值节点——DI1 内省）: `string / strings / boolean / booleans / nil(Boolean) / timestamp(String) / timestamps / number(Float) / numbers / ref(AnalyticsSelectFieldEnum) / from(String) / variable(String) / function_with_args / arg_name`

**variable 引用链**（修正旧"variables 死参数"结论——活引用点 = right.variable）:
```
right: { variable: "v1" } + variables: [{ key: "v1", value: "new" }]  → 1（引用链活——value 替换达 SQL）
variable value = "new' --" → 0 正常执行（value 走 bind——注入闭）
```

**ref-ref 列值比较**（right.ref 可用——DI5/DJ6）:
```
right.ref 同列(state eq state) → 7（恒真——同类型列引用工作）
right.ref 异列(state eq report_id) → GraphQL 层 Query execution error（类型推断崩——服务端缺陷记录）
```

**nil/timestamp 值通道**: `right.nil: true` → 0（eq NULL 语义）；`right.timestamp: "2026-08-27 06:47:03 UTC"` → 0（bind 语义正常）

**limit 0**: 无错返回空 values（对照 DB7 limit -1 报 "between 1 and 5000"——0 绕过下限 = 校验不一致——服务端缺陷记录）

## 九、另一 AI 建议对照矩阵（已测/类型层闭/待测）

### P0-1 纯 or 无主条件——类型层不可构造 + fail-open 已排除
- AnalyticsWhereInputType 仅 predicates（CV1）；or 只在 AnalyticsWherePredicateInputType 内（DF1）且 left/function/right 全 NON_NULL → 纯 or/残缺谓词在 GraphQL 校验层即拒（CX2/CX3 同型错误形态）
- fail-open 排除：多元素 or 丢弃时主条件保留（DG4=1/DG6=0/DG7=0/DG9=0——主条件 0 匹配结果仍 0 非全表）；uniq 后单元素/嵌套正常（DG2/DG3/DG5/DG8/DH1）
- where omitted = AX 全表矩阵覆盖；or: [] 空列表 = DG10（主条件生效）；predicates: [] ≈ omitted（已覆盖）

### P0-3 and/or 混合嵌套——单层已测，深层多元素未测
- and 字段不存在（顶层 predicates = 隐式 AND——CV1）
- **待测**: 内层多元素 or（or[A, or[B,C 多元素]]——uniq 是全局展开还是逐层判别）→ DK7

### P0-4 uid 缓存碰撞——未测
- CW5 仅多 uid 独立并行正常
- **待测**: 同 uid 双 query（允许+空权限同请求）→ DK3；顺序复用（先允许后空）→ DK8

### P1-1 聚合/原始路径矩阵——大部分已测，三缺口
- 已测: count / sum(null) / 原始值 / order_by / limit / offset / join / or / select.where / select.from / variables
- **待测**: count distinct（select.distinct 从未使用）→ DK6；min/max/avg 空权限表 → DK11
- group_by 字段不存在（CW1 全结构无）；interval 分桶（month/day 多行形态）→ DK12（低）

### P1-2 join 方向——反向未测
- 允许主 join 空表恒真 = 0（BE5）；join 结构无 on/left（DI2——with/type/where/as）
- **待测**: 空权限表为主表 join 允许表 + select 允许表字段（RLS 双向注入判别）→ DK4

### P1-3 from/字段错配——select.from 已测，query.from 未测
- select.from 错配 = 纯装饰不覆盖来源（CU1-5——field 前缀决定列归属）
- **待测（最高价值）**: query.from 与 field 前缀错配——全部历史测试均同表，RLS 依据表 vs SQL 表未判别 → DK1/DK2

### P1-4 排序侧信道——非法 key 已测，合法无权限列未测
- 非法/追加/引号/反引号/简写 key = NoMethodError 字典全串匹配（CZ3-5/DB1-4/DC1-2——无 SQL 泄露）
- **待测**: 合法存在但无权限表列作 key（字典 hit 后 SQL 生成路径）→ DK5

### P2 项——全部已闭（无需重测）
- NoMethodError 消息无路径/栈/SQL（CZ/DB/DC）
- limit/offset: -1 拒 / 0 空返 / 负 offset 拒 / 上限 5000（DB7/DC5/DJ5）；5001 未测（低价值）
- benchmark AUTHORIZATION 铁壁（BZ-CB）/ having 结构损坏（DA）/ 引号注释 default 整数解析（CR-CS）

## 十、待测方向清单（DK 系列——按优先级）
```
DK1  query.from=空权限表(dim_reports) + field=允许表(dim_hacker_reports)   RLS 依据 vs SQL 表
DK2  query.from=允许表 + field=空权限表列（反向）
DK3  同 uid 双 query（允许表 + 空权限表同请求）——uid 缓存/复用判别
DK4  空权限表为主表 join 允许表恒真 + select 允许表字段——RLS 双向注入
DK5  order_by key = 空权限表合法列（字典 hit）
DK6  select.distinct: true（SELECT DISTINCT / count distinct 判别）
DK7  嵌套 or 内层多元素（uniq 逐层 vs 全局）
DK8  同 uid 顺序复用（看 DK3 结果再发）
DK11 min/max/avg 空权限表（并入批量）
DK12 interval month 分桶行数（并入批量）
```

## 十一、DK 系列结果（2026-09-09——表集合校验/uid 机制/聚合路径收官）

### DK1/DK2 from-field 错配——表集合校验层拒绝（闭）
```
query.from: dim_reports + field: dim_hacker_reports__report_id
→ Query table 'dim_hacker_reports' not available in this context（GraphQL 层）
query.from: dim_hacker_reports + field: dim_reports__report_id
→ Query table 'dim_reports' not available in this context（对称）
```
**新防御机制确认**: field 前缀表必须 ∈ {from} ∪ {join.with}（join 时跨表 field 可用——BE 系列已证）——RLS 依据表与 SQL 表分离不可构造

### DK4 反向 join——RLS 双向注入（闭）
```
from: dim_reports(空) + join dim_hacker_reports 恒真 + select dim_hacker_reports 字段 → 0
```

### DK5 order_by 空权限表合法列——表集合校验后崩（闭）
```
order_by.key: dim_reports__report_id（字典 hit——列存在）
→ NoMethodError: undefined method '+' for nil（表集合 miss → nil → 崩）
```
精确修正: order_by key 先查全局字段字典（hit），再查当前查询表集合（miss = nil = NoMethodError）——与非法 key 同型错误

### DK6 distinct——活字段（非死参数）
```
select: [{ field: state, distinct: true }]（原始值）→ 3 行去重（not-applicable/duplicate/new）
= SELECT DISTINCT 形态——新 SQL 分支确认
```

### DK7 嵌套 or 内层多元素——uniq 逐层执行（闭）
```
主 new + or[dup 内嵌 or[na, closed]] → 2（new+dup）
内层多元素先丢弃 → 外层单元素生效 = uniq 逐层递归（非全局展开）——最坏 = 更少数据
```

### DK3/DK9 同 uid 双 query——请求内注册表冲突（500）
```
同 uid 不同内容 / 同 uid 完全相同内容 → 均 STANDARD_ERROR（GraphQL 层 500）
DI7 崩溃根因修正 = uid 重复（非 limit 0——DJ5 已排除）
```
**uid = 请求内注册表键**（DataPoint.uid 与 query 匹配用）——重复即未捕获异常——服务端缺陷记录

### DK8 跨请求 uid——无状态（闭）
```
uid kc1: 允许表 7 → 空表 0（不复用）
uid kc2: 空表 0 → 允许表 7（反向不复用）
```
无持久缓存层——uid 缓存碰撞/复用彻底闭

### DK11 聚合批量——RLS 全覆盖（闭）
```
dim_reports: min/max/avg = [null, null, null]；count+distinct = "0"
多 select 形态确认: keys = [mn,mx,av,cd] as 列表, values = 单行多列
```

### DK12 interval month——不分桶（闭）
```
month 与 year 同: 单行聚合（允许表 7/空表 0）——interval 只做时间窗对齐不产生分组行
```

### 服务端缺陷累积清单（DK 新增标注——均无泄露）
1. 同请求重复 uid → 500（注册表冲突未捕获）
2. right.ref 异列类型推断崩 → GraphQL 层 500（DI5）
3. limit 0 绕过下限校验（返回空非报错——对照 -1 报 "between 1 and 5000"）
4. having 翻译器代码与 schema 类型不匹配（DA——NoMethodError 'ref'）
5. or 多元素静默丢弃（过滤过度方向）
6. order_by 表集合 miss = NoMethodError 未优雅处理
7. default 非整数字符串 = GraphQL 层崩（CR2-6/CS5-6）
8. benchmark interval "year" → 500（值域非法未捕获——BY1/BY2）

## 十二、EL→FI 系列归档（2026-09-10——单表全通道收官）

> 说明：ET/EU/EV 为 Report 对象线探索（activities/协作者读取），经用户指正后放弃，勿再测。以下为 dim_hacker_reports 单表全部结果。

### ES 谓词函数 12 全矩阵
- 活 8：eq / not_eq / lt（=1 行）/ lteq（=1 行）/ gt（=6 行）/ gteq / in / not_in——比较家族与真实分布吻合
- 崩 4：any / not_any / overlap（系）——schema 注册但执行不支持（缺陷）
- date_trunc 左值：NULL 空转（恒不匹配——8a=8b=0 双探针）

### 左值形态
- ref 活（唯一正常路径）；function 部分 NULL 空转
- 裸值（string/number/boolean/timestamp/arg_name/variable）全崩——FJ5 证据：`NoMethodError: undefined method 'eq' for true`（翻译器=对象方法链模式，裸值无 eq 方法）

### 聚合矩阵（8+3）
- count/sum/min/max/avg/count_distinct 活；p50c/p50d 活（=20.0）；array_agg 活（返回 7 个自家 id，与可见行一致——零越权）
- date_add/date_trunc arguments 参数死（[{string}]/[{number}]/[{ref}] 三形态均返回原值）

### join 结构
- 单 join = 49（7²）；双 join = 343（7³）；恒假 join = 0——数学全吻合
- join.where 必填（EX6/EX7）；with_variable 不存在（argumentNotAccepted）

### EW 否定语义/括号（空权限表判别）
- not_eq / not_in / 单元素 or / 双嵌套 or / 混合 全 0；允许表同构构造 = 7（判别力成立）
- or 多元素 uniq 后丢弃（过滤过度方向——安全）

### EZ 分页/RLS 顺序
- offset 0/1/2 行序正确（空/1 行 3914617/2 行）
- select.where 聚合内条件 = 0/7（RLS 正确）；空表 EZ4 空

### FA→FG 别名注入判决（核心系列）
- select.as：锚定白名单 `[A-Za-z][A-Za-z0-9_]*`（"ab c"/"a1,1"/"a1,submitted_at" 三连拒）
- join.as：**无任何校验**（"j1 x"=49——与 select.as 防御不一致）
- 引号行为：as=`j1"x` → GraphQL 层 Query execution error（未包装）；`,`/`--`/`'` → 49（引号包裹内合法标识符）
- FD/FE/FG 升级尝试（`j1" ON false -- ` / `j1""x` / `j1""` 等 26 样本）：**含 `"` 全崩、不含全安全**——`"` 在到达 SQL 前经引号敏感层零容忍处理——**无中间态可利用**
- **判决：join.as 无校验但不可利用（缺陷记录）——此门关闭**

### FF variables key
- "a1 x" / `a1"` 均正常（1 行）——无校验但 bind 不进 SQL

### FJ/FI 值类型全矩阵（ComplexInputType 用完）
- right.boolean → 0（bind）；right.from → 0（值语义，未变表引用）
- right.timestamps → `TypeError: can't quote Array`（**quote 转义环节物理证据**）
- right.numbers / booleans → `NoMethodError: to_f for Array`（复数家族 3/3 未实现）
- left.boolean → `NoMethodError: 'eq' for true`；left.timestamp → GraphQL 层未捕获崩
- interval year/quarter/month/week 全正常（不分桶）；列名枚举边界：updated_at/bounty_amount/weakness/title 不在 AnalyticsSelectFieldEnum

### FI1b 全列 RLS 终验
- 10 列实值读取：reporter_id 7 行全部 = 4421190（仅自己）——全列归属一致，零越权

### FH 时序侧信道
- T7/T0/TE 各 4 次：366-582ms 全重叠——无信号（关闭）

## 十三、防御模型终版（均有实验证据）

1. 枚举/字典校验：表/列/函数/别名（select.as / order_by.key / field 前缀表集合 ∈ {from}∪{join.with}）
2. quote 转义：全部值类型（FJ3 物理证据）
3. 对象方法链：left 只收复杂对象，裸值全崩（FJ5）
4. 引号敏感层：join.as 的 `"` 全崩（26 样本）
5. RLS 行级：谓词/or/join/聚合/原始值/分页/distinct/时间窗/全列 全覆盖
6. bind/注册表：uid、variables 不进 SQL
7. 过滤过度方向：or 多元素丢弃（安全方向）
8. **唯一"无校验且进 SQL"= join.as——引号崩兜底——不可利用**

## 十四、服务端缺陷累积（EA→FI 新增——全部无泄露类）

9. 谓词 4 函数执行不支持（any/not_any/overlap 系）
10. 复数数组 3/3 未实现（timestamps/numbers/booleans → quote/to_f 崩）
11. left 裸值全崩（NoMethodError 无方法）
12. left.timestamp GraphQL 层未捕获崩
13. join.as 无白名单校验（防御不一致——不可利用）
14. date_add/date_trunc arguments 参数死
15. interval 校验不一致（benchmark 非法值 500 vs query 正常）

## 十五、GL→GH 系列归档（2026-09-10——order_by 机制/default/limit/arguments/内省全量收口）

### having 终判（缺陷——面关闭）
- 三形态全崩：DA 式 / 完整式（field+function+as）/ 仅 field——全 `NoMethodError 'ref' for AnalyticsSelectInputType`
- 类型层信息：having.predicates[].left 类型 = AnalyticsSelectInputType（field 必填、ref 不被接受）
- 判决：having 翻译器代码与 schema 不匹配——聚合后过滤子句不可达——闭

### select.as 正则修正
- 单字符 as（"r"/"s"）被拒：`alias should match [A-Za-z][A-Za-z0-9_]`——首字母后必须至少 1 个后续字符
- 修正版：`[A-Za-z][A-Za-z0-9_]+`——GK1 假阴性真因，闭

### order_by 输出列名匹配机制（本窗口最大机制发现）
- 结构：`{ key: String!, direction: AnalyticsDirectionEnum! }`；direction 值域 {asc, desc} **小写**（DESC/ASC/ascending 类型层拒——大小写敏感）
- 机制：**key 必须精确匹配 select 输出列名**（有 as = as 值；无 as = 字段全名）
  - 匹配 → 排序生效（升降序正确）；miss → nil → `NoMethodError '+' for nil` 崩
- 验证六连：GS1（无 as + 字段全名 ✓倒序）/ GS2（as c1 + key"c1" ✓）/ GS3（key"c2" ✓按时间倒序）/ GS4（key 不在输出列 ✗崩）/ GT1（聚合 as"cc"+key"cc" ✓7）/ GT2（join+聚合 ✓49）
- 历史之谜解：当年"倒序生效"= 无 as 形态；GL2→GN3 全崩 = 有 as 而 key 用字段名
- 辅助事实：order_by: [] 空数组不触发处理链（正常）；含 `"`/任何非匹配 key 一律崩
- 判决：机制安全无注入面（精确字符串比对 + 列对象引用 + 方向枚举）

### limit 面（闭）
- limit: 2 → 精确 2 行；limit: -1 → `Query limit has to be between 1 and 5000`（服务层自定义校验，上限 5000）
- Int 类型 + 范围校验——无注入面

### default 机制（安全——闭）
- 语义：`COALESCE(col, '<v>')`——值字符串包裹 + 按列类型转换（PG unknown literal 语义）
- 证据链：`"x"`+bigint 崩（转换失败）/ `"1"`+bigint|text 正常 / `"Z'Z"`|`"Z''Z"`+text 正常（未转义必解析崩——没崩=转义正确）/ `"Z'Z"`+bigint 崩（回归类型转换）
- 判决：字符串安全转义（或 bind）——无注入面

### arguments 死参终判（date_trunc/date_add）
- date_trunc + [{string:"month"}] → 全 null；+ [{number:1}] → 全 null（若真进 SQL 应报 date_trunc(int,ts) 类型错——没崩=参数位恒 NULL）
- date_add + [{number:1}] → 输出原值（未 +1 天）
- 判决：位置参数恒 NULL/fallback——无注入面（对照：ref 参数正常——array_agg ref ✓）

### 函数矩阵收格
- array_agg：PG 数组字面量输出 {..}（ref 生效）✓
- p50c：精确中位数（3955363 = 7 值中位）✓
- 派生列：submitted_at_week → 周一起始时间戳；submitted_at_month → 月首（bucket 时间戳而非序号）

### 内省全量清单（__type 开放；限制：≤3 别名/选择集）
- QueryInput 13 字段：uid/start_at!/end_at!/interval!/select!/from!/join/having/where/order_by/limit/offset/variables
- SelectInput 8 字段：field!/from(String)/function/function_with_args/as/default/distinct(Bool)/where
- JoinInput 4 字段：with!/type!/where!（必填）/as
- FunctionInput：{name: SelectFunctionEnum, arguments: [ComplexInputType!], ref: SelectFieldEnum}
- QueryVariableInput：{key!, value!}；OrderByInput：{key!, direction!}；HavingInput：{predicates!, operator!}；WhereInput：{predicates!}
- 值域：OperatorEnum={and,or}；IntervalEnum={day,week,month,quarter,year}；DirectionEnum={asc,desc}；JoinTypeEnum={inner,outer}；SelectFunctionEnum={sum,min,max,avg,p50c,p50d,count,array_agg,date_trunc,date_add}；FromEnum=29 表
- dim_hacker_reports 全 18 列：reporter_id/report_id/team_id/team_handle/is_valid_report/state/severity_rating/asset_type/engagement_type/weakness_name/submitted_at(+_year/_quarter/_month/_week/_day/_num_days_since)/total_bounty_amount

### 多查询/interval 补格
- interval 值域 5 值全正常（day/week/month/quarter/year）；双查询完全隔离（q1=7/q2=0 独立 uid/values）
- 7 行数据特征：severity critical×5/high/none；engagement_type 全 BUG_BOUNTY；weakness_name 全非空（无 NULL 行）

### 谓词/输出面全穷尽（GI/GJ 收尾）
- 谓词元素真名 AnalyticsWherePredicateInputType：left!/function!/right!/or（or = 历史"静默忽略"字段所在）
- 谓词函数 12 全值域：eq/not_eq/lt/lteq/gt/gteq/in/not_in/any/not_any/overlap/not_overlap（与历史 12 矩阵吻合：活 8+崩 4）
- 返回类型 AnalyticsDataPoint 8 字段：uid! / has_error! / error_class / error_message / keys! / values! / id! / sql
- **id = 瞬态 GID**（gid://hackerone/Objects::AnalyticsDataPoint/<UUID>——每次执行 UUID 变化——不可引用）
- **sql = 死字段**（正常路径 null / Ruby 异常路径 null / PG 错路径无数据点——三路径全无填充）
- **错误路径二分**：Ruby 异常（捕获→has_error=true 数据点）vs PG 错误（未捕获→整查询 null "Query execution error"）
- 旁证：AnalyticsQueryResult 类型（benchmarkName/errorType/keys/queryKey/values——benchmark/内部类型，记录不追）；did-you-mean 错误机制（hasError→has_error）
- **收官：输入面 25/25 参数位 + 输出面 8/8 字段全穷尽**

### GK 完美构造实测（整装验证——2026-09-10）
- GK2（无聚合版）：join(7×) + where + order_by c1 desc + limit 500 + offset + variables + 原始列 → **49 行原始笛卡尔、降序生效** ✓
- GK3（混合列，无 join）：原始列 + count 混排可用——**隐式 GROUP BY 原始列、cc=1**（组内行数）
- GK4：`default: "ZZ"` 在 timestamp 列 → `Query execution error`（'ZZ'::timestamp 失败）——**default 铁律：值必须可转列类型**
- GK5（完美构造 v2）：全参数整装 → **7 行、c1 降序、cc=7**（join 组内计数） ✓
- **语义收获：混合 select = 隐式 GROUP BY 原始列 + count(*)=组内行数**（GK3=1 / GK5=7 双验证）；无聚合 = 原始笛卡尔（GK2=49）
- **完美构造 v2 = 全参数可用最终形态**：所有查询参数（除 having）和谐共存，唯一约束 = order_by key 匹配输出列名 + default 值类型兼容 + as 正则

### 谓词值类型矩阵与时间过滤能力（JA→JF——2026-09-10 收尾）
- **右值五类型全可用**：number ✓ / timestamp ✓ / string ✓ / boolean ✓ / ref ✓
- **复数形态（列表）非死区——是 in/not_in 的专属正确形态**：numbers/strings/timestamps 列表在 in/not_in 下精确执行（JG2/JH2/JI2 验证）；比较类函数（lt/gt 等）配复数才崩
- **in/not_in 真活复核（JG→JJ）**：单值/复数/文本/桶列全验证——**8/8 函数真活收官**（eq/not_eq/lt/lteq/gt/gteq/in/not_in）
- **ref vs ref 复核（JK）**：列间比较（如 report_id > team_id）/恒真（ref eq ref）均精确执行——**谓词面 100% 穷尽（函数×左值×右值三维全收）**
- **亚秒墙（JJ 定案）**：时间列显示层截秒（"04:14:58 UTC"）、实际值带非零亚秒——秒级等值 in/eq 恒 0 行（不崩、静默不匹配）；**时间列过滤唯一可靠路径 = 范围卡（gt/lt/gteq/lteq）**；桶列整点值无亚秒→等值可用
- **新能力①：时间列直接 ISO 时间过滤**——submitted_at gt/gteq/lt/lteq {timestamp:"..."} 真比较、精确边界（lt 反向断言=0 行；gteq 08-20 精确 5 行）
- **新能力②：时间桶列配桶起始时间戳**——month eq "2026-09-01T00:00:00Z" 精确 1 行；year 桶列 lteq 桶值正常——**JD5 崩因闭环：number 2026 喂 timestamp 桶 → 跨类型 PG 崩**
- **新能力③：string/boolean 精确匹配**——state eq {string:"new"} 1 行；is_valid_report eq {boolean:false} 7 行
- **第五条铁律：值类型必须匹配列类型**——跨类型（timestamp 桶 vs number）→ Query execution error
- **谓词函数真活复核**：eq（主列/数字派生列/桶列/文本列/布尔列全活）、gt/gteq/lt/lteq 真执行——8 函数确认（in/not_in 历史活；any/not_any/overlap/not_overlap 崩）
- **JA/JB：join.as 字符结论**——可用字符集=除 `"` 外全部；`'`/`--`/引号对/自洽逃逸/悬空全测——逃逸型构造全崩（无注入面）
- **JF 收尾**：五类条件同链共存（1 行精确命中）；纯时间区间4进3出（跨日边界精确）

## 十六、服务端缺陷累积（GL→GH 新增——无泄露类）
16. order_by 输出列名匹配 miss 未优雅处理（`'+' for nil` 崩——缺陷 6 同族：字典/匹配链 miss）
17. having 翻译器代码-schema 不匹配（补全缺陷 4 证据：三形态全崩）

## 十七、最终封版（2026-09-10 晚——全参数树完成 + 跨表连接矩阵 + 防御终判）

### 值节点 14 字段实弹闭幕（ComplexInputType 全穷尽）
- strings/numbers/booleans/timestamps = in/not_in 专属数组载体（JG-JI 已录）；比较函数配复数崩
- **not_in 补集对称终验**：in+numbers 对 state 列 = 0 行 ↔ not_in+numbers = 全 7 行（N4a）；not_in+strings["draft"] = 7 行（7 行中无 draft）——肯定/否定路径严格对称
- variable 未绑定差异：主谓词 = 0 行（静默）；or 分支 = 只废该分支（V2b=1 行 draft）——均安全方向
- function_with_args：date_add 可执行但**参数不参与计算**（M 系列 2days=1day 逐字节相同、注入 payload 零变化）——参数通道闭

### 谓词 × nil 全矩阵（统一）
- eq+nil = 0 / not_eq+nil = 全行（IS NULL / IS NOT NULL 语义正确）
- gt/lt/gteq/lteq+nil = 全 0 行——比较类 nil 统一不匹配（T3/T4）

### 类型错位审计（DSL 无静态类型校验——下沉 DB 宽松转换）
- gt+boolean（数值列）= true 隐式当 1：num_index>true → 2/3/4/5 共 4 行（T5a）
- in+numbers 对字符串 state 列 = 0 行不崩（T5b）；not_in 对称全行（N4a）
- 结论：无上层校验、DB 隐式转换执行；无越权读、无错误泄露——实现瑕疵级（缺陷 18）

### or 规则终版（顶层 where 与 join.where 完全一致——全场景实测）
1. uniq 后恰 1 个谓词 → 生效；2. 不同谓词 ≥2 → 整节点静默丢弃；3. 空数组 → 忽略
4. 嵌套逐层判别（内层先丢）；多 predicate 各自单元素 or = 隐式 AND 叠加正常（P4=2 行）
- **join.where 同规则三数据点**：T7a 无 or = 72 行 / T7b 单元素 or = 12 行 / T1 双元素 or = 0 行——自洽闭环

### Join 连接矩阵（四向全通——连接分组认知修正）
- dim↔dim ✅（X1）；fixture↔fixture ✅（T7a=72=12×6 精确）
- fixture 主表→dim join ✅（X9 不崩，0 行归因 or 丢弃）；dim 主表→fixture join ✅（X10=42=7×6 全笛卡尔积精确）
- **唯一崩塌点 = 查询级 from 重绑定**（from=fixture 表 + dim 列引用 → "not available in this context"/执行崩）——**上下文集切换器 = 隔离唯一执行点**；join 跨域双向全通（功能性组合，所涉表均无敏感数据）
- 术语澄清：查询级 from（上下文集切换 + 严格校验）≠ 谓词 ref.from（别名引用；非别名内容静默忽略——P5）

### 表可见性矩阵收口（29 表 FromEnum）
- 有数据 6 张全公开字典/统计：fixture_report_states(12)/fixture_severity_ratings(6)/fct_platform_benchmarks(20+)/dim_surveys(8+)/dim_survey_structured_responses(45)/fct_bounty_table_cohorts(200/150) + 自有 dim_hacker_reports(7)
- 其余全部：RLS 0 行 / 跨 connection 崩（mv_dim_reports、fixture_intervals 直查）
- 主表列名裁决：state 存在（3991685=new，T6a）；closed_at 不存在（非枚举成员）——外部清单列名必须逐条枚举验证

### 封版终判
三层防御完整：①枚举硬校验（29 表 / 556 列 / 10+12 函数 / 函数×列配对 / 别名正则 / ref 前缀表 ∈ {from}∪join.with）②全值 bind（string/number/boolean/timestamp/in 元素/variables/函数参数 七路交叉证实）③RLS 全覆盖。
注入面不存在；残余低危不可利用：or 丢弃（方向安全）/ having NoMethodError / connection 报错 / date_trunc null / dim_surveys__id 崩 / 类型宽松。
**不再投入**：not_in/not_any 变体（对称已证）、overlap/any（无数组列载体）、uid/interval 元字段健壮性（非数据面）。

## 十八、服务端缺陷累积（本轮新增）
18. 类型无静态校验——type-mismatch 值直接下沉 DB（gt+boolean 静默执行生效；实现瑕疵）
19. 部分表无 __id 伪列且单列 select 崩（dim_surveys__id 类——R0 枚举发现）
