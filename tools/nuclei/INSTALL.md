# 📥 Nuclei 安装指南

## ⚠️ 重要说明

由于Nuclei可执行文件较大（约25MB），**未包含在Git仓库中**。请按照以下步骤下载。

---

## 🚀 快速安装

### **方法1：使用自动安装脚本（推荐）**

```bash
python tools/setup_tools.py
```

脚本会自动检查并提示你下载所需的工具。

### **方法2：手动下载**

1. 访问 Nuclei 官方发布页面：
   https://github.com/projectdiscovery/nuclei/releases/latest

2. 下载适合你系统的版本：
   - **Windows**: `nuclei_XXX_windows_amd64.zip`
   - **Linux**: `nuclei_XXX_linux_amd64.zip`
   - **macOS**: `nuclei_XXX_darwin_amd64.zip`

3. 解压并将 `nuclei.exe` (Windows) 或 `nuclei` (Linux/Mac) 放到：
   ```
   D:\scan\tools\nuclei\
   ```

4. 验证安装：
   ```bash
   tools/nuclei/nuclei.exe -version
   ```

---

## 📋 完整工具清单

### **必需工具**

| 工具 | 状态 | 安装方式 |
|------|------|----------|
| **Nuclei** | ⚠️ 需下载 | 见上方说明 |
| **Wappalyzer** | ✅ Python包 | `pip install python-Wappalyzer` |

### **可选工具**

| 工具 | 用途 | 安装方式 |
|------|------|----------|
| **Nmap** | 端口扫描 | 从 https://nmap.org/download.html 下载 |
| **SQLMap** | SQL注入测试 | `pip install sqlmap` 或从官网下载 |

---

## 🔧 验证安装

运行测试脚本：

```bash
python test_ai.py
```

这会检查所有依赖和工具是否正确安装。

---

## ❓ 常见问题

### Q1: 为什么不把Nuclei放在Git里？
**A:** 
- 文件太大（25MB+），会让仓库变得臃肿
- 可以从官方快速获取最新版本
- 不同平台需要不同版本

### Q2: 下载速度慢怎么办？
**A:** 
- 使用国内镜像：https://ghproxy.com/
- 或者使用迅雷等下载工具

### Q3: 如何更新Nuclei？
**A:** 
```bash
tools/nuclei/nuclei.exe -update
```

或者重新下载最新版本。

### Q4: 没有Nuclei能使用项目吗？
**A:** 
可以！但只能使用技术栈检测功能，无法进行漏洞扫描。

---

## 💡 提示

首次运行 `automate_scan.py` 时，脚本会自动尝试更新Nuclei模板：

```bash
python automate_scan.py
```

如果Nuclei未找到，会显示提示信息。

---

**安装完成后，就可以开始使用了！** 🚀
