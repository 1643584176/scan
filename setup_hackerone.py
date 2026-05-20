#!/usr/bin/env python3
"""
HackerOne API 配置助手
帮助用户快速配置 HackerOne API Token
"""

import os
import sys


def print_banner():
    """打印欢迎横幅"""
    print("="*60)
    print("HackerOne API 配置助手")
    print("="*60)
    print()


def check_existing_config():
    """检查现有配置"""
    env_file = '.env'
    
    if os.path.exists(env_file):
        print("[INFO] 发现现有的 .env 文件")
        
        # 读取现有配置
        config = {}
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        
        if 'HACKERONE_API_TOKEN' in config:
            token = config['HACKERONE_API_TOKEN']
            masked_token = token[:10] + '...' if len(token) > 10 else '***'
            print(f"  - API Token: {masked_token}")
        
        if 'HACKERONE_USERNAME' in config:
            print(f"  - 用户名: {config['HACKERONE_USERNAME']}")
        
        print()
        return config
    else:
        print("[INFO] 未找到 .env 文件，将创建新的配置文件\n")
        return {}


def get_hackerone_username():
    """获取 HackerOne 用户名"""
    print("-"*60)
    print("步骤 1: 输入你的 HackerOne 用户名")
    print("-"*60)
    print()
    print("提示：")
    print("  - 在你的个人主页 URL 中可以看到")
    print("  - 例如：https://hackerone.com/YOUR_USERNAME")
    print()
    
    username = input("请输入用户名: ").strip()
    
    if not username:
        print("[ERROR] 用户名不能为空")
        return None
    
    return username


def get_hackerone_token():
    """获取 HackerOne API Token"""
    print()
    print("-"*60)
    print("步骤 2: 输入你的 HackerOne API Token")
    print("-"*60)
    print()
    print("如何获取 Token：")
    print("  1. 登录 HackerOne")
    print("  2. 访问: https://hackerone.com/settings/api_token")
    print("  3. 点击 'Generate new token'")
    print("  4. 复制生成的 Token（只显示一次！）")
    print()
    print("⚠️  重要：Token 会保密存储，不会泄露")
    print()
    
    token = input("请输入 API Token: ").strip()
    
    if not token:
        print("[ERROR] Token 不能为空")
        return None
    
    if len(token) < 20:
        print("[WARN] Token 看起来太短，请确认是否正确")
        confirm = input("是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            return None
    
    return token


def save_config(username, token):
    """保存配置到 .env 文件"""
    env_file = '.env'
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# HackerOne API 配置\n")
            f.write("# 注意：此文件包含敏感信息，已添加到 .gitignore，不会提交到 Git\n")
            f.write("\n")
            f.write("# HackerOne API Token\n")
            f.write("# 获取方式：https://hackerone.com/settings/api_token\n")
            f.write(f"HACKERONE_API_TOKEN={token}\n")
            f.write("\n")
            f.write("# HackerOne 用户名\n")
            f.write(f"HACKERONE_USERNAME={username}\n")
        
        print()
        print("[OK] 配置已保存到 .env 文件")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 保存配置失败: {e}")
        return False


def verify_config():
    """验证配置"""
    print()
    print("-"*60)
    print("验证配置")
    print("-"*60)
    print()
    
    # 检查环境变量
    token = os.environ.get('HACKERONE_API_TOKEN')
    username = os.environ.get('HACKERONE_USERNAME')
    
    if token and username:
        print("[OK] 环境变量已设置")
        print(f"  - 用户名: {username}")
        print(f"  - Token: {token[:10]}...")
        
        # 尝试导入并测试
        try:
            sys.path.insert(0, 'tools')
            from hackerone_api import HackerOneAPI
            
            print("\n[INFO] 正在测试 API 连接...")
            client = HackerOneAPI()
            
            # 获取项目列表
            programs = client.get_programs()
            print(f"[OK] API 连接成功！")
            print(f"     找到 {len(programs)} 个项目")
            
            if programs:
                first_program = programs[0]['attributes']['handle']
                print(f"     示例项目: {first_program}")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] API 测试失败: {e}")
            print("\n可能的原因：")
            print("  1. Token 无效或已过期")
            print("  2. 用户名不正确")
            print("  3. 网络连接问题")
            return False
    else:
        print("[ERROR] 环境变量未设置")
        return False


def main():
    """主函数"""
    print_banner()
    
    # 检查现有配置
    existing_config = check_existing_config()
    
    # 询问是否重新配置
    if existing_config:
        reconfigure = input("是否重新配置？(y/n): ").strip().lower()
        if reconfigure != 'y':
            print("\n[INFO] 使用现有配置")
            # 验证现有配置
            verify_config()
            return
    
    print()
    
    # 获取用户名
    username = get_hackerone_username()
    if not username:
        print("\n[ERROR] 配置取消")
        return
    
    # 获取 Token
    token = get_hackerone_token()
    if not token:
        print("\n[ERROR] 配置取消")
        return
    
    # 保存配置
    if save_config(username, token):
        print("\n" + "="*60)
        print("配置完成！")
        print("="*60)
        print()
        print("下一步：")
        print("  1. 验证配置: python tools/hackerone_api.py")
        print("  2. 开始扫描: python automate_scan.py")
        print("  3. 学习报告: python tools/vuln_report_learner.py XSS")
        print()
        
        # 立即验证
        verify = input("是否立即验证配置？(y/n): ").strip().lower()
        if verify == 'y':
            # 重新加载环境变量
            os.environ['HACKERONE_API_TOKEN'] = token
            os.environ['HACKERONE_USERNAME'] = username
            verify_config()
    else:
        print("\n[ERROR] 配置保存失败")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] 配置已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
