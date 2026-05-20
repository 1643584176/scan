#!/usr/bin/env python3
"""
快速测试脚本 - 验证项目简化后的功能
"""

import sys
import os
import subprocess


def print_section(title):
    """打印分隔线"""
    print("\n" + "="*60)
    print(title)
    print("="*60 + "\n")


def test_python_dependencies():
    """测试 Python 依赖"""
    print_section("1. 测试 Python 依赖")
    
    dependencies = ['requests', 'bs4']
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✓ {dep} 已安装")
        except ImportError:
            print(f"✗ {dep} 未安装")
            return False
    
    return True


def test_go_tools():
    """测试 Go 工具"""
    print_section("2. 测试 Go 工具")
    
    tools = ['nuclei', 'httpx', 'katana']
    
    for tool in tools:
        try:
            result = subprocess.run(
                [tool, '-version'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                version_info = result.stdout.decode('utf-8', errors='ignore').strip()
                print(f"✓ {tool}: {version_info[:50]}")
            else:
                print(f"✗ {tool} 未正确安装")
                return False
        except FileNotFoundError:
            print(f"✗ {tool} 未找到")
            return False
        except Exception as e:
            print(f"✗ {tool} 检查失败: {e}")
            return False
    
    return True


def test_project_structure():
    """测试项目结构"""
    print_section("3. 测试项目结构")
    
    required_files = [
        'automate_scan.py',
        'simple_scan.py',
        'tools/go_tools.py',
        'tools/vuln_report_learner.py',
        'tools/hackerone_disclosed.py',
        'urls/targets.txt',
        'requirements.txt',
        'README.md',
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False
    
    return all_exist


def test_hackerone_integration():
    """测试 HackerOne 集成"""
    print_section("4. 测试 HackerOne 集成")
    
    # 检查是否配置了 API Token
    api_token = os.environ.get('HACKERONE_API_TOKEN')
    username = os.environ.get('HACKERONE_USERNAME')
    
    if api_token and username:
        print("✓ HackerOne API Token 已配置")
        print(f"  用户名: {username}")
        print(f"  Token: {api_token[:10]}...")
        
        # 尝试导入模块
        try:
            sys.path.insert(0, 'tools')
            from hackerone_disclosed import VulnerabilityReportLearner
            print("✓ HackerOne 模块导入成功")
            return True
        except Exception as e:
            print(f"✗ HackerOne 模块导入失败: {e}")
            return False
    else:
        print("ℹ HackerOne API 未配置（可选功能）")
        print("  要启用，请设置环境变量:")
        print("  - HACKERONE_API_TOKEN")
        print("  - HACKERONE_USERNAME")
        return True  # 这是可选功能


def test_vuln_report_learner():
    """测试漏洞报告学习工具"""
    print_section("5. 测试漏洞报告学习工具")
    
    try:
        sys.path.insert(0, 'tools')
        from vuln_report_learner import GoToolManager
        
        manager = GoToolManager()
        print("✓ 漏洞报告学习工具导入成功")
        
        # 检查工具状态
        tools_status = {}
        for tool_name in ['nuclei', 'httpx', 'katana']:
            tools_status[tool_name] = manager.check_tool_installed(tool_name)
            status = "✓" if tools_status[tool_name] else "✗"
            print(f"  {status} {tool_name}")
        
        return all(tools_status.values())
        
    except Exception as e:
        print(f"✗ 漏洞报告学习工具测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print_section("🔍 项目简化验证测试")
    
    results = {
        'Python 依赖': test_python_dependencies(),
        'Go 工具': test_go_tools(),
        '项目结构': test_project_structure(),
        'HackerOne 集成': test_hackerone_integration(),
        '漏洞报告学习': test_vuln_report_learner(),
    }
    
    # 打印总结
    print_section("📊 测试总结")
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 所有测试通过！项目简化成功！")
        print("\n下一步:")
        print("  1. 在 urls/targets.txt 中添加目标 URL")
        print("  2. 运行: python automate_scan.py")
        print("  3. 或运行: python simple_scan.py")
    else:
        print("⚠️  部分测试失败，请检查上述错误")
        print("\n建议:")
        if not results['Python 依赖']:
            print("  - 运行: pip install -r requirements.txt")
        if not results['Go 工具']:
            print("  - 运行: python tools/go_tools.py install")
        if not results['项目结构']:
            print("  - 检查文件是否完整")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
