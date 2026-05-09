#!/usr/bin/env python3
"""
AI记忆共享服务器 - 社区版（带许可证控制）
允许用户上传和下载匿名的AI学习成果，实现互帮互助
需要有效许可证才能使用共享功能
"""

import os
import json
import hashlib
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse
from license_manager import LicenseManager


class SharedMemoryServer:
    """共享记忆服务器（带许可证验证）"""
    
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.shared_db_path = 'shared_memory_db.json'
        self.shared_db = self._load_shared_db()
        self.license_manager = LicenseManager()
        
    def _load_shared_db(self):
        """加载共享数据库"""
        if os.path.exists(self.shared_db_path):
            try:
                with open(self.shared_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "version": "1.0",
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "contributions": [],
            "global_patterns": {},
            "statistics": {
                "total_contributors": 0,
                "total_scans_shared": 0,
                "last_updated": None
            }
        }
    
    def save_shared_db(self):
        """保存共享数据库"""
        with open(self.shared_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.shared_db, f, indent=2, ensure_ascii=False)
    
    def anonymize_data(self, data):
        """匿名化数据 - 移除敏感信息"""
        anonymized = {
            "tech_stack": data.get('tech_stack', []),
            "vuln_types": [],
            "risk_level": data.get('risk_level', 'unknown'),
            "risk_score": data.get('risk_score', 0),
            "timestamp": data.get('timestamp', ''),
            "contribution_id": hashlib.md5(
                f"{data.get('domain', '')}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]
        }
        
        # 提取漏洞类型（不包含具体URL或描述）
        for vuln in data.get('analyzed_vulns', []):
            anonymized['vuln_types'].append({
                'type': vuln.get('type', 'unknown'),
                'severity': vuln.get('severity', 'info'),
                'confidence': vuln.get('confidence', 0.5)
            })
        
        return anonymized
    
    def contribute_memory(self, local_kb):
        """贡献本地记忆到共享库（需要许可证）"""
        # 检查许可证
        allowed, message = self.license_manager.can_share_memory()
        if not allowed:
            print(f"\n❌ {message}")
            print("💡 请运行 python license_manager.py 激活许可证")
            return 0
        
        print("\n📤 正在准备贡献数据...")
        
        contributions = []
        for scan_record in local_kb.get('scan_history', []):
            # 匿名化处理
            anon_data = self.anonymize_data(scan_record)
            contributions.append(anon_data)
        
        # 添加到共享库
        self.shared_db['contributions'].extend(contributions)
        self.shared_db['statistics']['total_contributors'] += 1
        self.shared_db['statistics']['total_scans_shared'] += len(contributions)
        self.shared_db['statistics']['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 更新全局模式
        self._update_global_patterns(contributions)
        
        self.save_shared_db()
        
        print(f"✅ 成功贡献 {len(contributions)} 条扫描记录")
        print(f"   贡献ID: {contributions[0]['contribution_id'] if contributions else 'N/A'}")
        
        return len(contributions)
    
    def _update_global_patterns(self, contributions):
        """更新全局漏洞模式统计"""
        for contrib in contributions:
            for vuln in contrib.get('vuln_types', []):
                vuln_type = vuln['type']
                if vuln_type not in self.shared_db['global_patterns']:
                    self.shared_db['global_patterns'][vuln_type] = {
                        'count': 0,
                        'avg_confidence': 0,
                        'severity_distribution': {}
                    }
                
                pattern = self.shared_db['global_patterns'][vuln_type]
                pattern['count'] += 1
                pattern['avg_confidence'] = (
                    (pattern['avg_confidence'] * (pattern['count'] - 1) + vuln['confidence']) 
                    / pattern['count']
                )
                
                severity = vuln['severity']
                pattern['severity_distribution'][severity] = \
                    pattern['severity_distribution'].get(severity, 0) + 1
    
    def get_community_wisdom(self):
        """获取社区智慧 - 全局统计"""
        stats = self.shared_db['statistics']
        patterns = self.shared_db['global_patterns']
        
        print("\n" + "="*60)
        print("🌍 社区智慧统计")
        print("="*60)
        print(f"\n📊 总体数据:")
        print(f"   - 贡献者数量: {stats['total_contributors']}")
        print(f"   - 共享扫描数: {stats['total_scans_shared']}")
        print(f"   - 最后更新: {stats['last_updated'] or '从未'}")
        
        if patterns:
            print(f"\n🔥 全球最常见漏洞类型:")
            sorted_patterns = sorted(
                patterns.items(), 
                key=lambda x: x[1]['count'], 
                reverse=True
            )
            
            for i, (vuln_type, data) in enumerate(sorted_patterns[:10], 1):
                avg_conf = data['avg_confidence']
                print(f"   {i}. {vuln_type}")
                print(f"      出现次数: {data['count']}")
                print(f"      平均置信度: {avg_conf:.0%}")
                print(f"      严重程度分布: {data['severity_distribution']}")
        
        print()
        
        return {
            'statistics': stats,
            'patterns': patterns
        }
    
    def download_wisdom(self):
        """下载社区智慧到本地（需要许可证）"""
        # 检查许可证
        allowed, message = self.license_manager.can_download_wisdom()
        if not allowed:
            print(f"\n❌ {message}")
            print("💡 请运行 python license_manager.py 激活许可证")
            return None
        
        if not self.shared_db['contributions']:
            print("❌ 共享库为空，暂无可下载的数据")
            return None
        
        print(f"\n📥 正在准备下载社区智慧...")
        print(f"   可用数据: {len(self.shared_db['contributions'])} 条记录")
        
        # 生成可导入的格式
        wisdom_package = {
            "exported_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "source": "community_shared_memory",
            "contributions": self.shared_db['contributions'],
            "global_patterns": self.shared_db['global_patterns']
        }
        
        output_file = f"community_wisdom_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(wisdom_package, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 社区智慧已导出: {output_file}")
        print(f"   使用 python manage_memory.py 导入此文件\n")
        
        return output_file
    
    def start_server(self):
        """启动HTTP服务器（用于远程共享）"""
        class SharedMemoryHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/api/stats':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        self.server.shared_db['statistics'],
                        ensure_ascii=False
                    ).encode())
                elif self.path == '/api/download':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(
                        self.server.shared_db,
                        ensure_ascii=False
                    ).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_POST(self):
                if self.path == '/api/contribute':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode())
                    
                    count = self.server.contribute_memory(data)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'success',
                        'contributed_count': count
                    }).encode())
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # 静默日志
        
        server = HTTPServer((self.host, self.port), SharedMemoryHandler)
        server.shared_db = self.shared_db
        
        print(f"\n🌐 共享记忆服务器启动于 http://{self.host}:{self.port}")
        print(f"API端点:")
        print(f"  - GET  /api/stats     - 查看统计")
        print(f"  - GET  /api/download  - 下载完整数据")
        print(f"  - POST /api/contribute - 贡献数据")
        print(f"\n按 Ctrl+C 停止服务器\n")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")
            server.server_close()


def interactive_cli():
    """交互式命令行界面"""
    server = SharedMemoryServer()
    
    print("\n" + "="*60)
    print("🌍 AI记忆共享系统 - 社区版")
    print("="*60 + "\n")
    
    while True:
        print("选择操作:")
        print("1. 查看社区智慧统计")
        print("2. 贡献我的学习成果（匿名）")
        print("3. 下载社区智慧")
        print("4. 启动共享服务器（高级）")
        print("0. 退出")
        
        choice = input("\n请选择 [0-4]: ").strip()
        
        if choice == '1':
            server.get_community_wisdom()
        
        elif choice == '2':
            if not os.path.exists('knowledge_base.json'):
                print("❌ 本地没有记忆数据，请先运行扫描")
                continue
            
            with open('knowledge_base.json', 'r', encoding='utf-8') as f:
                local_kb = json.load(f)
            
            confirm = input(f"将贡献 {len(local_kb.get('scan_history', []))} 条记录（匿名处理），确认？(yes/no): ")
            if confirm.lower() == 'yes':
                count = server.contribute_memory(local_kb)
                print(f"\n🎉 感谢你的贡献！帮助了社区其他人")
            else:
                print("已取消")
        
        elif choice == '3':
            server.download_wisdom()
        
        elif choice == '4':
            print("\n⚠️  这将启动HTTP服务器，允许其他人连接")
            confirm = input("确认启动？(yes/no): ")
            if confirm.lower() == 'yes':
                server.start_server()
            else:
                print("已取消")
        
        elif choice == '0':
            print("\n再见！感谢为社区做贡献 🌟")
            break
        
        else:
            print("无效选择")
        
        print()


if __name__ == "__main__":
    interactive_cli()
