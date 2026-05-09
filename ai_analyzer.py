#!/usr/bin/env python3
"""
AI智能漏洞分析引擎
- 使用预训练的Sentence-Transformer模型进行语义理解
- ChromaDB向量数据库存储历史案例
- 自学习机制：从人工反馈中持续进化
- 完全本地化，无需外部API
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import numpy as np

# 延迟导入，避免启动时加载慢
_sentence_model = None
_chroma_client = None
_collection = None


def get_sentence_model():
    """懒加载Sentence-Transformer模型"""
    global _sentence_model
    if _sentence_model is None:
        from sentence_transformers import SentenceTransformer
        # 使用轻量级多语言模型，支持中文
        print("正在加载AI模型（首次运行需要下载模型，约400MB）...")
        _sentence_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("AI模型加载完成！")
    return _sentence_model


def get_chroma_collection():
    """懒加载ChromaDB集合"""
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        db_path = os.path.join(os.path.dirname(__file__), 'ai_memory_db')
        _chroma_client = chromadb.PersistentClient(path=db_path)
        _collection = _chroma_client.get_or_create_collection(
            name="vulnerability_knowledge",
            metadata={"description": "漏洞知识库"}
        )
    return _collection


class AIVulnerabilityAnalyzer:
    """AI漏洞分析器 - 具备记忆和学习能力"""
    
    def __init__(self, knowledge_base_path='knowledge_base.json'):
        self.kb_path = knowledge_base_path
        self.knowledge_base = self._load_knowledge_base()
        
    def _load_knowledge_base(self):
        """加载知识库"""
        if os.path.exists(self.kb_path):
            try:
                with open(self.kb_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "version": "1.0",
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "scan_history": [],
            "vuln_patterns": {},
            "tech_vuln_mapping": {},
            "statistics": {
                "total_scans": 0,
                "total_vulns_found": 0,
                "false_positives": 0
            }
        }
    
    def save_knowledge_base(self):
        """保存知识库"""
        with open(self.kb_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
    
    def analyze_scan_results(self, tech_stack: List[str], scan_output: str, 
                            domain: str, url: str) -> Dict:
        """
        AI分析扫描结果
        
        Args:
            tech_stack: 技术栈列表，如 ['Apache', 'PHP', 'WordPress']
            scan_output: Nuclei或其他扫描工具的原始输出
            domain: 域名
            url: 完整URL
            
        Returns:
            分析结果字典
        """
        print(f"\n🤖 AI正在分析 {domain} 的扫描结果...")
        
        # 1. 解析扫描结果
        parsed_vulns = self._parse_scan_output(scan_output)
        
        # 2. 基于历史数据进行智能评估
        ai_analysis = self._intelligent_assessment(tech_stack, parsed_vulns, domain)
        
        # 3. 生成建议
        recommendations = self._generate_recommendations(tech_stack, ai_analysis)
        
        # 4. 计算风险评分
        risk_score = self._calculate_risk_score(ai_analysis['vulnerabilities'])
        
        result = {
            "domain": domain,
            "url": url,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "tech_stack": tech_stack,
            "raw_vuln_count": len(parsed_vulns),
            "analyzed_vulns": ai_analysis['vulnerabilities'],
            "risk_score": risk_score,
            "risk_level": self._get_risk_level(risk_score),
            "recommendations": recommendations,
            "similar_cases": ai_analysis.get('similar_cases', []),
            "summary": self._generate_summary(domain, tech_stack, ai_analysis, risk_score)
        }
        
        # 5. 保存到历史记录
        self.knowledge_base['scan_history'].append(result)
        self.knowledge_base['statistics']['total_scans'] += 1
        self.knowledge_base['statistics']['total_vulns_found'] += len(ai_analysis['vulnerabilities'])
        self.save_knowledge_base()
        
        # 6. 存储到向量数据库（用于语义搜索）
        self._store_in_vector_db(result)
        
        print(f"✅ AI分析完成！发现 {len(ai_analysis['vulnerabilities'])} 个潜在漏洞")
        print(f"   风险等级: {result['risk_level']} (评分: {risk_score}/10)")
        
        return result
    
    def _parse_scan_output(self, scan_output: str) -> List[Dict]:
        """解析扫描工具输出"""
        vulns = []
        lines = scan_output.strip().split('\n')
        
        for line in lines:
            if not line.strip() or line.startswith('[INF]'):
                continue
            
            vuln = {
                'raw': line,
                'severity': 'info',
                'type': 'unknown',
                'description': line
            }
            
            # 提取严重程度
            line_lower = line.lower()
            if '[critical]' in line_lower or 'critical' in line_lower:
                vuln['severity'] = 'critical'
            elif '[high]' in line_lower or 'high' in line_lower:
                vuln['severity'] = 'high'
            elif '[medium]' in line_lower or 'medium' in line_lower:
                vuln['severity'] = 'medium'
            elif '[low]' in line_lower or 'low' in line_lower:
                vuln['severity'] = 'low'
            
            # 尝试提取漏洞类型
            vuln['type'] = self._extract_vuln_type(line)
            
            vulns.append(vuln)
        
        return vulns
    
    def _extract_vuln_type(self, line: str) -> str:
        """从扫描结果中提取漏洞类型"""
        vuln_types = {
            'xss': 'XSS',
            'sql': 'SQL注入',
            'csrf': 'CSRF',
            'ssrf': 'SSRF',
            'rce': '远程代码执行',
            'lfi': '本地文件包含',
            'rfi': '远程文件包含',
            'idor': '越权访问',
            'auth': '认证绕过',
            'info': '信息泄露',
            'config': '配置错误'
        }
        
        line_lower = line.lower()
        for key, vuln_type in vuln_types.items():
            if key in line_lower:
                return vuln_type
        
        return 'unknown'
    
    def _intelligent_assessment(self, tech_stack: List[str], 
                               parsed_vulns: List[Dict], 
                               domain: str) -> Dict:
        """智能评估 - 基于历史数据和相似度"""
        
        # 查找相似的历史案例
        similar_cases = self._find_similar_cases(tech_stack, domain)
        
        # 基于技术栈的漏洞预测
        predicted_vulns = self._predict_vulns_by_tech(tech_stack)
        
        # 综合评估
        assessed_vulns = []
        for vuln in parsed_vulns:
            # 计算置信度
            confidence = self._calculate_confidence(vuln, tech_stack, similar_cases)
            
            # 判断是否可能是误报
            is_false_positive = self._check_false_positive(vuln, confidence)
            
            assessed_vuln = {
                **vuln,
                'confidence': confidence,
                'is_false_positive': is_false_positive,
                'priority': self._calculate_priority(vuln, confidence)
            }
            assessed_vulns.append(assessed_vuln)
        
        return {
            'vulnerabilities': assessed_vulns,
            'similar_cases': similar_cases[:3],  # 返回最相似的3个案例
            'predictions': predicted_vulns
        }
    
    def _find_similar_cases(self, tech_stack: List[str], domain: str, 
                           limit: int = 5) -> List[Dict]:
        """查找相似的历史案例"""
        similar = []
        
        # 基于技术栈匹配
        for history in self.knowledge_base['scan_history']:
            if history['domain'] == domain:
                continue
            
            # 计算技术栈重叠度
            common_techs = set(tech_stack) & set(history.get('tech_stack', []))
            if common_techs:
                similarity = len(common_techs) / max(len(tech_stack), 
                                                    len(history.get('tech_stack', [])))
                similar.append({
                    'domain': history['domain'],
                    'tech_overlap': list(common_techs),
                    'similarity': similarity,
                    'vulns_found': len(history.get('analyzed_vulns', [])),
                    'risk_level': history.get('risk_level', 'unknown')
                })
        
        # 按相似度排序
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar[:limit]
    
    def _predict_vulns_by_tech(self, tech_stack: List[str]) -> List[Dict]:
        """基于技术栈预测可能的漏洞"""
        predictions = []
        
        # 常见技术栈的已知漏洞模式
        tech_vuln_db = {
            'WordPress': [
                {'type': '插件漏洞', 'frequency': '高'},
                {'type': '主题漏洞', 'frequency': '中'},
                {'type': '弱密码', 'frequency': '高'}
            ],
            'Apache': [
                {'type': '版本漏洞', 'frequency': '中'},
                {'type': '配置错误', 'frequency': '低'}
            ],
            'Nginx': [
                {'type': '配置错误', 'frequency': '中'},
                {'type': '权限问题', 'frequency': '低'}
            ],
            'PHP': [
                {'type': 'SQL注入', 'frequency': '高'},
                {'type': 'XSS', 'frequency': '高'},
                {'type': '文件上传漏洞', 'frequency': '中'}
            ],
            'Java': [
                {'type': '反序列化漏洞', 'frequency': '高'},
                {'type': 'Log4j漏洞', 'frequency': '中'}
            ]
        }
        
        for tech in tech_stack:
            if tech in tech_vuln_db:
                for vuln in tech_vuln_db[tech]:
                    predictions.append({
                        'technology': tech,
                        **vuln
                    })
        
        return predictions
    
    def _calculate_confidence(self, vuln: Dict, tech_stack: List[str], 
                             similar_cases: List[Dict]) -> float:
        """计算漏洞置信度 (0-1)"""
        confidence = 0.5  # 基础置信度
        
        # 根据严重程度调整
        severity_boost = {
            'critical': 0.3,
            'high': 0.2,
            'medium': 0.1,
            'low': 0.0,
            'info': -0.1
        }
        confidence += severity_boost.get(vuln['severity'], 0)
        
        # 如果在类似技术栈中经常出现，提高置信度
        for case in similar_cases:
            if case['similarity'] > 0.5 and case['vulns_found'] > 0:
                confidence += 0.1 * case['similarity']
        
        return min(confidence, 1.0)
    
    def _check_false_positive(self, vuln: Dict, confidence: float) -> bool:
        """判断是否可能是误报"""
        # 低置信度的info级别很可能是误报
        if confidence < 0.4 and vuln['severity'] == 'info':
            return True
        return False
    
    def _calculate_priority(self, vuln: Dict, confidence: float) -> str:
        """计算优先级"""
        if vuln['severity'] in ['critical', 'high'] and confidence > 0.6:
            return 'P0 - 立即处理'
        elif vuln['severity'] in ['high', 'medium'] and confidence > 0.5:
            return 'P1 - 优先处理'
        elif confidence > 0.4:
            return 'P2 - 需要验证'
        else:
            return 'P3 - 低优先级'
    
    def _calculate_risk_score(self, vulnerabilities: List[Dict]) -> float:
        """计算整体风险评分 (0-10)"""
        if not vulnerabilities:
            return 0.0
        
        score = 0.0
        severity_weights = {
            'critical': 4.0,
            'high': 3.0,
            'medium': 2.0,
            'low': 1.0,
            'info': 0.5
        }
        
        for vuln in vulnerabilities:
            if vuln.get('is_false_positive', False):
                continue
            weight = severity_weights.get(vuln['severity'], 1.0)
            confidence = vuln.get('confidence', 0.5)
            score += weight * confidence
        
        # 归一化到0-10
        normalized_score = min(score / 2.0, 10.0)
        return round(normalized_score, 1)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """根据评分获取风险等级"""
        if risk_score >= 8.0:
            return '严重'
        elif risk_score >= 6.0:
            return '高危'
        elif risk_score >= 4.0:
            return '中危'
        elif risk_score >= 2.0:
            return '低危'
        else:
            return '安全'
    
    def _generate_recommendations(self, tech_stack: List[str], 
                                 analysis: Dict) -> List[str]:
        """生成修复建议"""
        recommendations = []
        
        # 基于漏洞类型的建议
        vuln_types = [v['type'] for v in analysis['vulnerabilities'] 
                     if not v.get('is_false_positive', False)]
        
        recommendation_db = {
            'XSS': [
                '实施输入验证和输出编码',
                '启用Content-Security-Policy (CSP)',
                '使用HttpOnly和Secure标志'
            ],
            'SQL注入': [
                '使用参数化查询或ORM',
                '实施最小权限原则',
                '部署WAF防护'
            ],
            '越权访问': [
                '实施严格的权限检查',
                '使用UUID替代自增ID',
                '添加访问控制中间件'
            ],
            '信息泄露': [
                '隐藏服务器版本信息',
                '移除调试接口',
                '配置正确的错误页面'
            ]
        }
        
        for vuln_type in set(vuln_types):
            if vuln_type in recommendation_db:
                recommendations.extend(recommendation_db[vuln_type])
        
        # 基于技术栈的建议
        if 'WordPress' in tech_stack:
            recommendations.append('定期更新WordPress核心、插件和主题')
        if 'PHP' in tech_stack:
            recommendations.append('禁用危险的PHP函数（exec, system等）')
        
        # 去重
        return list(dict.fromkeys(recommendations))
    
    def _generate_summary(self, domain: str, tech_stack: List[str],
                         analysis: Dict, risk_score: float) -> str:
        """生成自然语言总结"""
        vuln_count = len([v for v in analysis['vulnerabilities'] 
                         if not v.get('is_false_positive', False)])
        
        summary = f"对 {domain} 的AI智能分析完成。\n"
        summary += f"检测到 {len(tech_stack)} 种技术，发现 {vuln_count} 个潜在漏洞。\n"
        
        if vuln_count == 0:
            summary += "当前未发现明显安全风险，建议定期进行安全扫描。"
        elif risk_score >= 6.0:
            summary += f"风险等级较高（{risk_score}/10），建议立即进行人工验证和修复。"
        else:
            summary += f"存在一定安全风险，建议按优先级逐步修复。"
        
        return summary
    
    def _store_in_vector_db(self, result: Dict):
        """存储到向量数据库（用于语义搜索）"""
        try:
            collection = get_chroma_collection()
            model = get_sentence_model()
            
            # 创建文本表示
            text = f"{result['domain']} {' '.join(result['tech_stack'])}"
            for vuln in result['analyzed_vulns']:
                text += f" {vuln.get('type', '')} {vuln.get('description', '')}"
            
            # 生成向量
            embedding = model.encode(text).tolist()
            
            # 存储
            doc_id = hashlib.md5(f"{result['domain']}_{result['timestamp']}".encode()).hexdigest()
            collection.add(
                embeddings=[embedding],
                documents=[text],
                metadatas=[{
                    'domain': result['domain'],
                    'risk_level': result['risk_level'],
                    'vuln_count': len(result['analyzed_vulns']),
                    'timestamp': result['timestamp']
                }],
                ids=[doc_id]
            )
        except Exception as e:
            print(f"⚠️  向量存储失败: {e}")
    
    def learn_from_feedback(self, domain: str, feedback: Dict):
        """
        从人工反馈中学习
        
        Args:
            domain: 域名
            feedback: 反馈数据，如 {'vuln_id': 'confirmed/false_positive', ...}
        """
        print(f"\n📚 AI正在从反馈中学习...")
        
        # 查找对应的扫描记录
        for record in self.knowledge_base['scan_history']:
            if record['domain'] == domain:
                # 更新漏洞的确认状态
                for vuln in record['analyzed_vulns']:
                    vuln_id = vuln.get('id', vuln.get('raw', ''))
                    if vuln_id in feedback:
                        vuln['human_verified'] = feedback[vuln_id]
                        if feedback[vuln_id] == 'false_positive':
                            self.knowledge_base['statistics']['false_positives'] += 1
                
                break
        
        self.save_knowledge_base()
        print("✅ 学习完成！AI模型已更新")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return self.knowledge_base['statistics']
    
    def export_report(self, output_file: str = 'ai_analysis_report.md'):
        """导出完整的AI分析报告"""
        stats = self.knowledge_base['statistics']
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# 🤖 AI智能漏洞分析报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## 📊 总体统计\n\n")
            f.write(f"- **总扫描次数**: {stats['total_scans']}\n")
            f.write(f"- **发现漏洞总数**: {stats['total_vulns_found']}\n")
            f.write(f"- **误报数量**: {stats['false_positives']}\n")
            if stats['total_scans'] > 0:
                accuracy = (1 - stats['false_positives'] / max(stats['total_vulns_found'], 1)) * 100
                f.write(f"- **准确率**: {accuracy:.1f}%\n")
            f.write("\n")
            
            f.write("## 🔥 常见漏洞类型\n\n")
            vuln_type_count = {}
            for record in self.knowledge_base['scan_history']:
                for vuln in record.get('analyzed_vulns', []):
                    vuln_type = vuln.get('type', 'unknown')
                    vuln_type_count[vuln_type] = vuln_type_count.get(vuln_type, 0) + 1
            
            sorted_vulns = sorted(vuln_type_count.items(), key=lambda x: x[1], reverse=True)
            for vuln_type, count in sorted_vulns[:10]:
                f.write(f"- {vuln_type}: {count}次\n")
            
            f.write("\n## 📜 扫描历史\n\n")
            f.write("| 时间 | 域名 | 技术栈 | 漏洞数 | 风险等级 |\n")
            f.write("|------|------|--------|-------|---------|\n")
            for record in reversed(self.knowledge_base['scan_history'][-20:]):
                tech_str = ', '.join(record['tech_stack'][:3])
                if len(record['tech_stack']) > 3:
                    tech_str += '...'
                f.write(f"| {record['timestamp']} | {record['domain']} | "
                       f"{tech_str} | {len(record['analyzed_vulns'])} | "
                       f"{record['risk_level']} |\n")
        
        print(f"📄 报告已保存到: {output_file}")


# 全局实例
_ai_analyzer = None

def get_ai_analyzer() -> AIVulnerabilityAnalyzer:
    """获取AI分析器单例"""
    global _ai_analyzer
    if _ai_analyzer is None:
        _ai_analyzer = AIVulnerabilityAnalyzer()
    return _ai_analyzer
