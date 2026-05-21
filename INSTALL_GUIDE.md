# 依赖安装快速指南

## 🚀 快速开始（推荐）

### 一键安装所有依赖

```bash
python install_deps.py
```

这个脚本会自动：
1. ✅ 检查 Python 版本
2. ✅ 安装 Python 包（requests, beautifulsoup4, httpx 等）
3. ✅ 检查 Go 环境
4. ✅ 安装 Go 工具（katana, httpx, subfinder, nuclei）
5. ✅ 安装 SQLMap
6. ✅ 验证所有安装

---

## 📦 Python 依赖包

### 方法1：使用 pip 安装（标准）

```bash
pip install -r requirements.txt
```

### 方法2：手动安装

```bash
pip install requests>=2.31.0
pip install beautifulsoup4>=4.12.0
pip install urllib3>=2.0.0
pip install httpx>=0.24.0
```

---

## 🔧 外部工具安装

### 前置要求：安装 Go

**Windows:**
```powershell
# 下载安装包
# https://golang.org/dl/

# 或使用 Chocolatey
choco install golang
```

**macOS:**
```bash
brew install go
```

**Linux:**
```bash
sudo apt update
sudo apt install golang-go
```

**验证安装:**
```bash
go version
# 输出: go version go1.21.x ...
```

---

### 安装安全工具

#### 方法1：使用 Go 安装（推荐）

```bash
# Web 爬虫
go install github.com/projectdiscovery/katana/cmd/katana@latest

# HTTP 探测
go install github.com/projectdiscovery/httpx/cmd/httpx@latest

# 子域名枚举
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# 漏洞扫描
go install github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
```

#### 方法2：使用项目工具管理器

```bash
python tools/go_tools.py install katana
python tools/go_tools.py install httpx
python tools/go_tools.py install subfinder
python tools/go_tools.py install nuclei
```

#### 方法3：下载二进制文件

从 GitHub Releases 页面下载对应系统的二进制文件：
- [Katana Releases](https://github.com/projectdiscovery/katana/releases)
- [HTTPX Releases](https://github.com/projectdiscovery/httpx/releases)
- [Subfinder Releases](https://github.com/projectdiscovery/subfinder/releases)
- [Nuclei Releases](https://github.com/projectdiscovery/nuclei/releases)

下载后解压，将可执行文件添加到系统 PATH。

---

### 安装 SQLMap

**方法1：使用 pip（简单）**
```bash
pip install sqlmap
```

**方法2：从源码安装（推荐）**
```bash
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git
cd sqlmap
python sqlmap.py --version
```

**方法3：从官网下载**
```bash
# 访问 https://sqlmap.org 下载最新版本
```

---

## ✅ 验证安装

### 快速验证所有工具

```bash
python install_deps.py
```

这会运行完整的安装验证流程。

### 手动验证每个工具

```bash
# 检查 Python 包
python -c "import requests; print('requests OK')"
python -c "import bs4; print('beautifulsoup4 OK')"
python -c "import httpx; print('httpx OK')"

# 检查 Go 工具
katana -version
httpx -version
subfinder -version
nuclei -version

# 检查 SQLMap
sqlmap --version
# 或
python -m sqlmap --version
```

---

## 🐛 常见问题

### 问题1：`command not found: katana/httpx/subfinder/nuclei`

**原因：** Go 工具的 bin 目录不在 PATH 中

**解决方案：**

**Windows (PowerShell):**
```powershell
# 临时添加
$env:Path += ";$HOME\go\bin"

# 永久添加（需要重启终端）
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$HOME\go\bin", "User")
```

**macOS/Linux:**
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
source ~/.bashrc
```

### 问题2：Go 未安装

**错误信息：**
```
'go' 不是内部或外部命令，也不是可运行的程序
```

**解决方案：**
1. 下载并安装 Go：https://golang.org/dl/
2. 重启终端
3. 验证：`go version`

### 问题3：权限不足

**错误信息：**
```
permission denied
```

**解决方案：**

**Windows:**
```powershell
# 以管理员身份运行 PowerShell
```

**macOS/Linux:**
```bash
# 使用 sudo（谨慎）
sudo go install github.com/projectdiscovery/katana/cmd/katana@latest

# 或修改 GOPATH 权限
chmod -R 755 $HOME/go
```

### 问题4：网络问题导致下载失败

**错误信息：**
```
dial tcp: lookup github.com: no such host
```

**解决方案：**

设置 Go 代理：
```bash
# 使用国内代理
go env -w GOPROXY=https://goproxy.cn,direct

# 或使用官方代理
go env -w GOPROXY=https://proxy.golang.org,direct
```

### 问题5：SQLMap 安装失败

**解决方案：**
```bash
# 方法1：从 GitHub 克隆
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git
cd sqlmap
python sqlmap.py --version

# 方法2：使用 Docker
docker pull sqlmapproject/sqlmap
docker run --rm sqlmapproject/sqlmap --version
```

---

## 📋 完整安装清单

安装完成后，确认以下项目：

- [ ] Python 3.8+ 已安装
- [ ] Go 1.19+ 已安装
- [ ] Python 包已安装（requests, beautifulsoup4, httpx）
- [ ] katana 可用
- [ ] httpx 可用
- [ ] subfinder 可用
- [ ] nuclei 可用
- [ ] sqlmap 可用
- [ ] 所有工具的 PATH 配置正确

---

## 🎯 下一步

安装完成后：

1. **配置目标**
   ```bash
   # 编辑 urls/targets.txt，添加要扫描的目标
   echo "https://example.com" > urls/targets.txt
   ```

2. **运行扫描**
   ```bash
   python main.py
   ```

3. **查看结果**
   ```bash
   # 扫描结果保存在 @域名_bounty/ 目录
   ls @example.com_bounty/
   ```

---

## 📚 相关文档

- [README.md](README.md) - 项目主文档
- [PERFORMANCE_OPTIMIZATION.md](PERFORMANCE_OPTIMIZATION.md) - 性能优化说明
- [SECURITY_AND_INTELLIGENCE_OPTIMIZATION.md](SECURITY_AND_INTELLIGENCE_OPTIMIZATION.md) - 安全优化说明
- [SUBDOMAIN_SCAN_GUIDE.md](SUBDOMAIN_SCAN_GUIDE.md) - 子域名扫描指南

---

*最后更新: 2026-05-20*
