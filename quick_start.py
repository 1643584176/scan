#!/usr/bin/env python3
"""
快速开始脚本 - 新用户一键导入示例社区智慧
"""

import os
import sys


def quick_start():
    """快速开始向导"""
    print("\n" + "="*60)
    print("🚀 AI漏洞扫描系统 - 快速开始")
    print("="*60 + "\n")
    
    # 检查许可证状态
    from license_manager import LicenseManager
    license_mgr = LicenseManager()
    license_info = license_mgr.get_license_info()
    
    print(f"📋 许可证状态: {license_info['status']}")
    if license_info['status'] == '活跃':
        print(f"   类型: {license_info.get('type', 'N/A')}")
        print(f"   有效期至: {license_info.get('expires_at', 'N/A')}")
    else:
        print("   ⚠️  共享功能需要激活许可证")
        print("   运行: python license_manager.py activate")
    
    print()
    
    print("欢迎使用AI增强版漏洞扫描系统！\n")
    print("为了让你的AI立即具备智能分析能力，")
    print("我们为你准备了示例社区智慧数据。\n")
    
    # 检查是否已有记忆
    if os.path.exists('knowledge_base.json'):
        print("⚠️  检测到本地已有记忆数据")
        choice = input("是否导入示例社区智慧？(yes/no): ").strip().lower()
        if choice != 'yes':
            print("\n好的，你可以稍后手动导入。")
            print("运行: python import_community.py\n")
            return
    else:
        print("📦 即将导入示例社区智慧（5个匿名案例）...")
        print("这将帮助你的AI立即识别常见漏洞模式。\n")
    
    # 导入示例数据
    if not os.path.exists('example_community_wisdom.json'):
        print("❌ 示例文件不存在: example_community_wisdom.json")
        print("请确保该文件在项目根目录")
        return
    
    try:
        from import_community import import_community_wisdom
        success = import_community_wisdom('example_community_wisdom.json')
        
        if success:
            print("\n" + "="*60)
            print("🎉 恭喜！AI已准备好")
            print("="*60 + "\n")
            
            print("📖 下一步:")
            print("1. 在 urls/ 目录添加目标URL")
            print("   echo 'https://example.com' > urls/test.txt\n")
            
            print("2. 运行AI扫描")
            print("   python automate_scan.py\n")
            
            print("3. 查看智能报告")
            print("   打开 @example.com_bounty/findings.md\n")
            
            print("4. 训练AI（可选）")
            print("   python ai_feedback.py\n")
            
            print("\n💡 提示:")
            print("- 每次扫描后AI会自动学习")
            print("- 定期运行 share_memory.py 贡献经验")
            print("- 下载最新社区智慧保持AI更新\n")
            
            print("🌍 加入社区，互帮互助！")
            print("查看: 社区共享说明.md\n")
    
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("\n请确保已安装所有依赖:")
        print("pip install -r requirements.txt\n")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    quick_start()
