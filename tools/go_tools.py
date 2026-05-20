#!/usr/bin/env python3
"""
Go 工具管理器
自动安装和管理基于 Go 的安全扫描工具
"""

import subprocess
import sys
import os
import shutil


class GoToolManager:
    """管理 Go 编写的安全工具"""
    
    def __init__(self):
        self.tools = {
            'nuclei': {
                'package': 'github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest',
                'check_cmd': 'nuclei -version',
                'description': '漏洞扫描器'
            },
            'httpx': {
                'package': 'github.com/projectdiscovery/httpx/cmd/httpx@latest',
                'check_cmd': 'httpx -version',
                'description': 'HTTP 探测工具'
            },
            'katana': {
                'package': 'github.com/projectdiscovery/katana/cmd/katana@latest',
                'check_cmd': 'katana -version',
                'description': '爬虫工具'
            }
        }
        
    def check_go_installed(self):
        """检查 Go 是否已安装"""
        try:
            result = subprocess.run(
                ['go', 'version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✓ Go 已安装: {result.stdout.strip()}")
                return True
            else:
                print("✗ Go 未正确安装")
                return False
        except FileNotFoundError:
            print("✗ 未找到 Go，请先安装 Go: https://golang.org/dl/")
            return False
        except Exception as e:
            print(f"✗ 检查 Go 时出错: {e}")
            return False
    
    def check_tool_installed(self, tool_name):
        """检查工具是否已安装"""
        # 先尝试直接从 PATH 查找（优先）
        try:
            result = subprocess.run(
                [tool_name, '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # 尝试 GOBIN 路径
        gobin = os.environ.get('GOBIN')
        if gobin and os.path.exists(gobin):
            tool_path = os.path.join(gobin, f"{tool_name}.exe" if sys.platform == 'win32' else tool_name)
            if os.path.exists(tool_path):
                return True
        
        # 尝试 GOPATH/bin 路径
        gopath = os.environ.get('GOPATH')
        if not gopath:
            home = os.environ.get('USERPROFILE' if sys.platform == 'win32' else 'HOME')
            gopath = os.path.join(home, 'go')
        
        bin_dir = os.path.join(gopath, 'bin')
        tool_path = os.path.join(bin_dir, f"{tool_name}.exe" if sys.platform == 'win32' else tool_name)
        
        return os.path.exists(tool_path)
    
    def install_tool(self, tool_name):
        """安装单个 Go 工具"""
        if tool_name not in self.tools:
            print(f"✗ 未知工具: {tool_name}")
            return False
        
        tool_info = self.tools[tool_name]
        print(f"\n正在安装 {tool_name} ({tool_info['description']})...")
        
        try:
            # 设置国内 Go 代理
            env = os.environ.copy()
            env['GOPROXY'] = 'https://goproxy.cn,direct'
            env['GO111MODULE'] = 'on'
            
            # 使用 go install 安装
            result = subprocess.run(
                ['go', 'install', '-v', tool_info['package']],
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                env=env
            )
            
            if result.returncode == 0:
                print(f"✓ {tool_name} 安装成功")
                return True
            else:
                print(f"✗ {tool_name} 安装失败:")
                print(f"  {result.stderr[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"✗ {tool_name} 安装超时")
            return False
        except Exception as e:
            print(f"✗ {tool_name} 安装异常: {e}")
            return False
    
    def install_all_tools(self):
        """安装所有工具"""
        print("="*60)
        print("Go 安全工具安装器")
        print("="*60)
        
        # 检查 Go
        if not self.check_go_installed():
            return False
        
        # 检查并安装每个工具
        installed = 0
        total = len(self.tools)
        
        for tool_name, tool_info in self.tools.items():
            if self.check_tool_installed(tool_name):
                print(f"✓ {tool_name} 已安装")
                installed += 1
            else:
                if self.install_tool(tool_name):
                    installed += 1
        
        print("\n" + "="*60)
        print(f"安装完成: {installed}/{total} 个工具")
        print("="*60)
        
        return installed == total
    
    def update_all_tools(self):
        """更新所有工具到最新版本"""
        print("="*60)
        print("更新 Go 安全工具")
        print("="*60)
        
        if not self.check_go_installed():
            return False
        
        updated = 0
        for tool_name in self.tools.keys():
            print(f"\n更新 {tool_name}...")
            if self.install_tool(tool_name):
                updated += 1
        
        print(f"\n✓ 更新了 {updated} 个工具")
        return True
    
    def get_tool_path(self, tool_name):
        """获取工具路径（在 GOPATH/bin 或 GOBIN 中）"""
        # 优先使用 GOBIN
        gobin = os.environ.get('GOBIN')
        if gobin and os.path.exists(gobin):
            tool_path = os.path.join(gobin, f"{tool_name}.exe" if sys.platform == 'win32' else tool_name)
            if os.path.exists(tool_path):
                return tool_path
        
        # 使用 GOPATH/bin
        gopath = os.environ.get('GOPATH')
        if not gopath:
            # 默认 GOPATH
            home = os.environ.get('USERPROFILE' if sys.platform == 'win32' else 'HOME')
            gopath = os.path.join(home, 'go')
        
        bin_dir = os.path.join(gopath, 'bin')
        tool_path = os.path.join(bin_dir, f"{tool_name}.exe" if sys.platform == 'win32' else tool_name)
        
        if os.path.exists(tool_path):
            return tool_path
        
        # 尝试直接从 PATH 查找
        return tool_name  # 假设已在 PATH 中


def main():
    manager = GoToolManager()
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python go_tools.py install    - 安装所有工具")
        print("  python go_tools.py update     - 更新所有工具")
        print("  python go_tools.py check      - 检查工具状态")
        print("  python go_tools.py install <tool> - 安装指定工具")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'install':
        if len(sys.argv) > 2:
            # 安装指定工具
            tool = sys.argv[2]
            manager.install_tool(tool)
        else:
            # 安装所有工具
            manager.install_all_tools()
    
    elif command == 'update':
        manager.update_all_tools()
    
    elif command == 'check':
        print("工具状态检查:\n")
        for tool_name, tool_info in manager.tools.items():
            status = "✓ 已安装" if manager.check_tool_installed(tool_name) else "✗ 未安装"
            print(f"  {tool_name:10s} - {status} ({tool_info['description']})")
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
