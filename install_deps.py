#!/usr/bin/env python3
"""
一键安装所有依赖和工具
用法: python install_deps.py
"""
import sys
import os
import subprocess
import platform

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(text)
    print("="*60 + "\n")

def print_step(step, text):
    """打印步骤"""
    print(f"\n[{step}] {text}")
    print("-" * 60)

def run_command(cmd, description=""):
    """运行命令"""
    if description:
        print(f"   {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print(f"   ✓ 成功")
            return True
        else:
            print(f"   ✗ 失败: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"   ✗ 异常: {str(e)}")
        return False

def check_python_version():
    """检查 Python 版本"""
    print_step(1, "检查 Python 版本")
    
    version = sys.version_info
    print(f"   当前版本: Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ✗ Python 版本过低，需要 Python 3.8+")
        return False
    
    print("   ✓ Python 版本符合要求")
    return True

def install_python_packages():
    """安装 Python 包"""
    print_step(2, "安装 Python 依赖包")
    
    packages = [
        'requests>=2.31.0',
        'beautifulsoup4>=4.12.0',
        'urllib3>=2.0.0',
        'httpx>=0.24.0',
    ]
    
    for package in packages:
        success = run_command(
            f"{sys.executable} -m pip install {package}",
            f"安装 {package}"
        )
        if not success:
            print(f"   ⚠ 警告: {package} 安装失败，但继续执行")
    
    print("   ✓ Python 包安装完成")
    return True

def check_go_installed():
    """检查 Go 是否安装"""
    print_step(3, "检查 Go 环境")
    
    try:
        result = subprocess.run(
            'go version',
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"   {result.stdout.strip()}")
            print("   ✓ Go 已安装")
            return True
        else:
            print("   ✗ Go 未安装")
            print("\n   安装 Go:")
            print("   - Windows: https://golang.org/dl/")
            print("   - macOS: brew install go")
            print("   - Linux: sudo apt install golang-go")
            return False
    except:
        print("   ✗ 无法检测 Go")
        return False

def install_go_tools():
    """安装 Go 工具"""
    print_step(4, "安装 Go 安全工具")
    
    tools = [
        ('katana', 'github.com/projectdiscovery/katana/cmd/katana@latest', 'Web 爬虫'),
        ('httpx', 'github.com/projectdiscovery/httpx/cmd/httpx@latest', 'HTTP 探测'),
        ('subfinder', 'github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest', '子域名枚举'),
        ('nuclei', 'github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest', '漏洞扫描'),
    ]
    
    installed = []
    failed = []
    
    for tool_name, repo, description in tools:
        print(f"\n   安装 {tool_name} ({description})...")
        success = run_command(
            f'go install {repo}',
            f'正在安装 {tool_name}'
        )
        if success:
            installed.append(tool_name)
        else:
            failed.append(tool_name)
    
    print(f"\n   安装结果:")
    print(f"   ✓ 成功: {', '.join(installed) if installed else '无'}")
    if failed:
        print(f"   ✗ 失败: {', '.join(failed)}")
        print(f"\n   提示: 可以稍后手动安装失败的工具")
        print(f"   命令: go install github.com/projectdiscovery/{failed[0]}/cmd/{failed[0]}@latest")
    
    return len(failed) == 0

def install_sqlmap():
    """安装 SQLMap"""
    print_step(5, "安装 SQLMap")
    
    print("   尝试通过 pip 安装 sqlmap...")
    success = run_command(
        f'{sys.executable} -m pip install sqlmap',
        '安装 sqlmap'
    )
    
    if success:
        print("   ✓ SQLMap 安装成功")
        return True
    else:
        print("   ⚠ pip 安装失败")
        print("\n   替代方案:")
        print("   1. 从官网下载: https://sqlmap.org")
        print("   2. 从 GitHub 克隆: git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git")
        return False

def verify_installation():
    """验证安装"""
    print_step(6, "验证安装")
    
    tools_to_check = [
        ('python', '--version', 'Python'),
        ('katana', '-version', 'Katana'),
        ('httpx', '-version', 'HTTPX'),
        ('subfinder', '-version', 'Subfinder'),
        ('nuclei', '-version', 'Nuclei'),
    ]
    
    print("\n   检查工具可用性:\n")
    
    available = []
    missing = []
    
    for cmd, arg, name in tools_to_check:
        try:
            result = subprocess.run(
                f'{cmd} {arg}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0 or result.stdout or result.stderr:
                version_info = (result.stdout + result.stderr).strip().split('\n')[0][:80]
                print(f"   ✓ {name:15s} - {version_info}")
                available.append(name)
            else:
                print(f"   ✗ {name:15s} - 未找到")
                missing.append(name)
        except:
            print(f"   ✗ {name:15s} - 检查失败")
            missing.append(name)
    
    # 检查 SQLMap
    try:
        result = subprocess.run(
            f'{sys.executable} -m pip show sqlmap',
            shell=True,
            capture_output=True,
            text=True
        )
        if 'sqlmap' in result.stdout.lower():
            print(f"   ✓ SQLMap         - 已安装 (Python 包)")
            available.append('SQLMap')
        else:
            print(f"   ✗ SQLMap         - 未安装")
            missing.append('SQLMap')
    except:
        print(f"   ✗ SQLMap         - 检查失败")
        missing.append('SQLMap')
    
    print(f"\n   总结:")
    print(f"   - 可用工具: {len(available)} 个")
    print(f"   - 缺失工具: {len(missing)} 个")
    
    if missing:
        print(f"\n   缺失的工具: {', '.join(missing)}")
        print(f"\n   建议:")
        if 'Katana' in missing or 'HTTPX' in missing or 'Subfinder' in missing or 'Nuclei' in missing:
            print(f"   - 确保已安装 Go: https://golang.org/dl/")
            print(f"   - 运行: go install github.com/projectdiscovery/<tool>/cmd/<tool>@latest")
        if 'SQLMap' in missing:
            print(f"   - 运行: pip install sqlmap")
            print(f"   - 或从 https://sqlmap.org 下载")
    
    return len(missing) == 0

def main():
    """主函数"""
    print_header("自动化安全扫描器 - 依赖安装向导")
    
    print("本脚本将自动安装以下组件:")
    print("  1. Python 依赖包")
    print("  2. Go 安全工具 (Katana, HTTPX, Subfinder, Nuclei)")
    print("  3. SQLMap")
    print("\n预计时间: 5-15 分钟（取决于网络速度）")
    
    response = input("\n是否继续? (y/n): ").strip().lower()
    if response != 'y':
        print("已取消")
        sys.exit(0)
    
    # 执行安装步骤
    steps = [
        ("Python 版本检查", check_python_version),
        ("Python 包安装", install_python_packages),
        ("Go 环境检查", check_go_installed),
        ("Go 工具安装", install_go_tools),
        ("SQLMap 安装", install_sqlmap),
        ("安装验证", verify_installation),
    ]
    
    results = []
    for step_name, step_func in steps:
        try:
            result = step_func()
            results.append((step_name, result))
        except Exception as e:
            print(f"\n✗ {step_name} 发生错误: {e}")
            results.append((step_name, False))
    
    # 打印总结
    print_header("安装总结")
    
    all_success = all(result for _, result in results)
    
    for step_name, result in results:
        status = "✓ 成功" if result else "✗ 失败/跳过"
        print(f"  {status:10s} - {step_name}")
    
    print()
    if all_success:
        print("🎉 所有依赖安装成功！")
        print("\n下一步:")
        print("  1. 添加目标到 urls/targets.txt")
        print("  2. 运行: python main.py")
        print("\n查看文档:")
        print("  - README.md - 项目说明")
        print("  - SUBDOMAIN_SCAN_GUIDE.md - 子域名扫描指南")
        print("  - SECURITY_AND_INTELLIGENCE_OPTIMIZATION.md - 安全优化说明")
    else:
        print("⚠ 部分依赖安装失败")
        print("\n请查看上面的错误信息，手动安装缺失的组件")
        print("\n常用命令:")
        print("  - 安装 Go 工具: go install github.com/projectdiscovery/<tool>/cmd/<tool>@latest")
        print("  - 安装 SQLMap: pip install sqlmap")
        print("  - 验证安装: python install_deps.py")
    
    print()

if __name__ == '__main__':
    main()
