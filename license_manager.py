#!/usr/bin/env python3
"""
许可证管理系统 - 控制共享记忆功能的访问权限
支持激活码验证、有效期管理、功能分级
"""

import os
import json
import hashlib
import uuid
from datetime import datetime, timedelta


class LicenseManager:
    """许可证管理器"""
    
    def __init__(self, license_file='license.json'):
        self.license_file = license_file
        self.license = self._load_license()
    
    def _load_license(self):
        """加载许可证"""
        if os.path.exists(self.license_file):
            try:
                with open(self.license_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 默认未激活状态
        return {
            "activated": False,
            "license_key": None,
            "license_type": "none",
            "activated_at": None,
            "expires_at": None,
            "features": {
                "share_memory": False,
                "download_wisdom": False,
                "advanced_analysis": False,
                "priority_support": False
            },
            "hardware_id": None,
            "max_activations": 1,
            "activation_count": 0
        }
    
    def save_license(self):
        """保存许可证"""
        with open(self.license_file, 'w', encoding='utf-8') as f:
            json.dump(self.license, f, indent=2, ensure_ascii=False)
    
    def get_hardware_id(self):
        """获取硬件ID（用于绑定设备）"""
        # 基于机器特征生成唯一ID
        import platform
        import socket
        
        hardware_info = [
            platform.machine(),
            platform.node(),
            platform.processor(),
        ]
        
        # 尝试获取MAC地址
        try:
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                           for elements in range(0, 2*6, 2)][::-1])
            hardware_info.append(mac)
        except:
            pass
        
        hardware_str = '|'.join(hardware_info)
        return hashlib.sha256(hardware_str.encode()).hexdigest()[:32]
    
    def generate_license_key(self, license_type='basic', days_valid=365, max_activations=1):
        """
        生成许可证密钥（管理员使用）
        
        Args:
            license_type: 许可证类型 (basic/professional/enterprise)
            days_valid: 有效天数
            max_activations: 最大激活次数
            
        Returns:
            许可证密钥字符串
        """
        # 许可证配置
        configs = {
            'trial': {
                'days': 7,
                'features': {
                    'share_memory': False,
                    'download_wisdom': True,
                    'advanced_analysis': False,
                    'priority_support': False
                }
            },
            'basic': {
                'days': 365,
                'features': {
                    'share_memory': True,
                    'download_wisdom': True,
                    'advanced_analysis': False,
                    'priority_support': False
                }
            },
            'professional': {
                'days': 365,
                'features': {
                    'share_memory': True,
                    'download_wisdom': True,
                    'advanced_analysis': True,
                    'priority_support': True
                }
            },
            'enterprise': {
                'days': 99999,  # 永久
                'features': {
                    'share_memory': True,
                    'download_wisdom': True,
                    'advanced_analysis': True,
                    'priority_support': True
                }
            }
        }
        
        config = configs.get(license_type, configs['basic'])
        
        # 生成密钥内容
        secret = "YourSecretKey2026"  # 修改为你的密钥
        timestamp = datetime.now().isoformat()
        random_str = uuid.uuid4().hex[:16]
        
        key_content = f"{license_type}|{config['days']}|{max_activations}|{timestamp}|{random_str}"
        
        # 生成签名
        signature = hashlib.sha256(f"{key_content}{secret}".encode()).hexdigest()[:16]
        
        # 组合密钥
        license_key = f"{key_content}|{signature}"
        
        # Base64编码（简化版，实际可用base64库）
        import base64
        encoded_key = base64.b64encode(license_key.encode()).decode()
        
        print(f"\n✅ 许可证密钥生成成功！")
        print(f"\n许可证类型: {license_type.upper()}")
        print(f"有效期: {config['days']} 天")
        print(f"最大激活次数: {max_activations}")
        print(f"\n密钥:\n{encoded_key}\n")
        print("请将此密钥发送给客户\n")
        
        return encoded_key
    
    def activate(self, license_key):
        """
        激活许可证
        
        Args:
            license_key: 许可证密钥
            
        Returns:
            (success, message)
        """
        if self.license['activated']:
            return False, "许可证已激活，无需重复激活"
        
        try:
            # 解码密钥
            import base64
            decoded_key = base64.b64decode(license_key.encode()).decode()
            
            # 解析密钥内容
            parts = decoded_key.split('|')
            if len(parts) != 5:
                return False, "无效的许可证密钥格式"
            
            license_type = parts[0]
            days_valid = int(parts[1])
            max_activations = int(parts[2])
            timestamp = parts[3]
            random_str = parts[4]
            signature = parts[5] if len(parts) > 5 else ''
            
            # 验证签名
            secret = "YourSecretKey2026"  # 与生成时相同
            key_content = f"{license_type}|{days_valid}|{max_activations}|{timestamp}|{random_str}"
            expected_signature = hashlib.sha256(f"{key_content}{secret}".encode()).hexdigest()[:16]
            
            if signature != expected_signature:
                return False, "许可证密钥无效（签名验证失败）"
            
            # 检查激活次数
            if self.license['activation_count'] >= max_activations:
                return False, "已达到最大激活次数限制"
            
            # 激活许可证
            now = datetime.now()
            self.license.update({
                'activated': True,
                'license_key': license_key,
                'license_type': license_type,
                'activated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
                'expires_at': (now + timedelta(days=days_valid)).strftime('%Y-%m-%d %H:%M:%S'),
                'hardware_id': self.get_hardware_id(),
                'max_activations': max_activations,
                'activation_count': self.license['activation_count'] + 1
            })
            
            # 设置功能权限
            feature_configs = {
                'trial': {
                    'share_memory': False,
                    'download_wisdom': True,
                    'advanced_analysis': False,
                    'priority_support': False
                },
                'basic': {
                    'share_memory': True,
                    'download_wisdom': True,
                    'advanced_analysis': False,
                    'priority_support': False
                },
                'professional': {
                    'share_memory': True,
                    'download_wisdom': True,
                    'advanced_analysis': True,
                    'priority_support': True
                },
                'enterprise': {
                    'share_memory': True,
                    'download_wisdom': True,
                    'advanced_analysis': True,
                    'priority_support': True
                }
            }
            
            self.license['features'] = feature_configs.get(license_type, feature_configs['basic'])
            
            self.save_license()
            
            return True, f"许可证激活成功！类型: {license_type.upper()}, 有效期至: {self.license['expires_at']}"
        
        except Exception as e:
            return False, f"激活失败: {str(e)}"
    
    def check_feature_access(self, feature_name):
        """
        检查是否有权使用某个功能
        
        Args:
            feature_name: 功能名称 (share_memory/download_wisdom/advanced_analysis)
            
        Returns:
            (allowed, message)
        """
        if not self.license['activated']:
            return False, "功能未激活，请先激活许可证"
        
        # 检查有效期
        if self.license['expires_at']:
            expires = datetime.strptime(self.license['expires_at'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > expires:
                return False, f"许可证已过期（{self.license['expires_at']}）"
        
        # 检查功能权限
        if not self.license['features'].get(feature_name, False):
            return False, f"当前许可证不包含此功能（{self.license['license_type']}）"
        
        return True, "访问允许"
    
    def can_share_memory(self):
        """检查是否可以共享记忆"""
        return self.check_feature_access('share_memory')
    
    def can_download_wisdom(self):
        """检查是否可以下载社区智慧"""
        return self.check_feature_access('download_wisdom')
    
    def get_license_info(self):
        """获取许可证信息"""
        if not self.license['activated']:
            return {
                'status': '未激活',
                'message': '请运行 python license_manager.py activate 进行激活'
            }
        
        # 检查是否过期
        expired = False
        if self.license['expires_at']:
            expires = datetime.strptime(self.license['expires_at'], '%Y-%m-%d %H:%M:%S')
            expired = datetime.now() > expires
        
        return {
            'status': '已过期' if expired else '活跃',
            'type': self.license['license_type'].upper(),
            'activated_at': self.license['activated_at'],
            'expires_at': self.license['expires_at'],
            'features': self.license['features'],
            'hardware_id': self.license.get('hardware_id', 'N/A')
        }
    
    def deactivate(self):
        """停用许可证"""
        if not self.license['activated']:
            return False, "许可证未激活"
        
        self.license = {
            "activated": False,
            "license_key": None,
            "license_type": "none",
            "activated_at": None,
            "expires_at": None,
            "features": {
                "share_memory": False,
                "download_wisdom": False,
                "advanced_analysis": False,
                "priority_support": False
            },
            "hardware_id": None,
            "max_activations": 1,
            "activation_count": 0
        }
        
        self.save_license()
        return True, "许可证已停用"


def interactive_cli():
    """交互式命令行界面"""
    manager = LicenseManager()
    
    print("\n" + "="*60)
    print("🔑 许可证管理系统")
    print("="*60 + "\n")
    
    # 显示当前状态
    info = manager.get_license_info()
    print(f"当前状态: {info['status']}")
    if info['status'] == '活跃':
        print(f"许可证类型: {info['type']}")
        print(f"有效期至: {info['expires_at']}")
        print(f"\n功能权限:")
        for feature, enabled in info['features'].items():
            status = "✅ 已启用" if enabled else "❌ 未启用"
            print(f"  - {feature}: {status}")
    
    print("\n选择操作:")
    print("1. 激活许可证")
    print("2. 查看许可证信息")
    print("3. 生成许可证密钥（管理员）")
    print("4. 停用许可证")
    print("0. 退出")
    
    choice = input("\n请选择 [0-4]: ").strip()
    
    if choice == '1':
        key = input("请输入许可证密钥: ").strip()
        success, message = manager.activate(key)
        if success:
            print(f"\n✅ {message}")
        else:
            print(f"\n❌ {message}")
    
    elif choice == '2':
        info = manager.get_license_info()
        print(f"\n许可证信息:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    elif choice == '3':
        password = input("管理员密码: ").strip()
        # 简单密码保护（实际应该用更强的验证）
        if password == "admin123":  # 修改为你的密码
            license_type = input("许可证类型 [trial/basic/professional/enterprise]: ").strip()
            days = int(input("有效天数 [365]: ").strip() or "365")
            max_act = int(input("最大激活次数 [1]: ").strip() or "1")
            manager.generate_license_key(license_type, days, max_act)
        else:
            print("❌ 密码错误")
    
    elif choice == '4':
        confirm = input("确认停用许可证？(yes/no): ").strip().lower()
        if confirm == 'yes':
            success, message = manager.deactivate()
            print(f"\n{'✅' if success else '❌'} {message}")
    
    elif choice == '0':
        print("\n再见！")
        return
    
    else:
        print("无效选择")


if __name__ == "__main__":
    interactive_cli()
