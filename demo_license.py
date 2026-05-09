#!/usr/bin/env python3
"""
许可证系统演示脚本
展示如何生成和使用许可证
"""

from license_manager import LicenseManager
import time


def demo():
    """演示许可证系统"""
    print("\n" + "="*60)
    print("🔑 许可证系统演示")
    print("="*60 + "\n")
    
    manager = LicenseManager()
    
    # 1. 查看初始状态
    print("【步骤1】查看初始状态")
    info = manager.get_license_info()
    print(f"状态: {info['status']}")
    print(f"说明: {info.get('message', '')}\n")
    
    time.sleep(1)
    
    # 2. 生成一个基础版许可证
    print("【步骤2】管理员生成基础版许可证（模拟）")
    print("-" * 60)
    license_key = manager.generate_license_key('basic', 365, 1)
    
    time.sleep(2)
    
    # 3. 停用当前许可证（如果有的话）
    if manager.license['activated']:
        manager.deactivate()
    
    # 4. 激活许可证
    print("\n【步骤3】用户激活许可证")
    print("-" * 60)
    success, message = manager.activate(license_key)
    print(message)
    
    time.sleep(1)
    
    # 5. 查看激活后的状态
    print("\n【步骤4】查看激活后的状态")
    print("-" * 60)
    info = manager.get_license_info()
    print(f"状态: {info['status']}")
    print(f"类型: {info.get('type', 'N/A')}")
    print(f"有效期: {info.get('expires_at', 'N/A')}")
    print(f"\n功能权限:")
    for feature, enabled in info.get('features', {}).items():
        status = "✅ 已启用" if enabled else "❌ 未启用"
        print(f"  - {feature}: {status}")
    
    time.sleep(1)
    
    # 6. 测试功能访问
    print("\n【步骤5】测试功能访问权限")
    print("-" * 60)
    
    allowed, msg = manager.can_share_memory()
    print(f"共享记忆: {'✅ 允许' if allowed else '❌ 禁止'} - {msg}")
    
    allowed, msg = manager.can_download_wisdom()
    print(f"下载智慧: {'✅ 允许' if allowed else '❌ 禁止'} - {msg}")
    
    allowed, msg = manager.check_feature_access('advanced_analysis')
    print(f"高级分析: {'✅ 允许' if allowed else '❌ 禁止'} - {msg}")
    
    time.sleep(1)
    
    # 7. 生成不同类型的许可证对比
    print("\n【步骤6】生成不同类型许可证对比")
    print("="*60)
    
    print("\n生成试用版许可证...")
    manager.generate_license_key('trial', 7, 1)
    
    print("\n生成专业版许可证...")
    manager.generate_license_key('professional', 365, 1)
    
    print("\n生成企业版许可证...")
    manager.generate_license_key('enterprise', 99999, 5)
    
    print("\n" + "="*60)
    print("✅ 演示完成！")
    print("="*60 + "\n")
    
    print("📖 使用说明:")
    print("1. 运行 python license_manager.py")
    print("2. 选择 '3. 生成许可证密钥'（管理员）")
    print("3. 将密钥发送给用户")
    print("4. 用户选择 '1. 激活许可证'")
    print("5. 激活成功后即可使用共享功能\n")


if __name__ == "__main__":
    demo()
