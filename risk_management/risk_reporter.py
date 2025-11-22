"""
风险报告生成器
生成详细的风险分析报告
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from .risk_engine import RiskMetrics, RiskAlert

logger = logging.getLogger(__name__)


class RiskReporter:
    """风险报告生成器"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_risk_report(self, risk_metrics: RiskMetrics, 
                          alerts: List[RiskAlert], 
                          portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成完整风险报告"""
        try:
            report = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'report_version': '1.0',
                    'period': '24h'
                },
                'risk_metrics': self._format_risk_metrics(risk_metrics),
                'risk_alerts': self._format_alerts(alerts),
                'portfolio_analysis': self._analyze_portfolio(portfolio_data),
                'risk_recommendations': self._generate_recommendations(risk_metrics, alerts),
                'compliance_check': self._check_compliance(risk_metrics, alerts)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成风险报告失败: {e}")
            return {}
    
    def _format_risk_metrics(self, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """格式化风险指标"""
        if not risk_metrics:
            return {}
        
        return {
            'value_at_risk': {
                'var_95': f"{risk_metrics.var_95:.2%}",
                'var_99': f"{risk_metrics.var_99:.2%}",
                'interpretation': '在95%置信度下，单日最大预期损失'
            },
            'drawdown_metrics': {
                'max_drawdown': f"{risk_metrics.max_drawdown:.2%}",
                'interpretation': '历史最大回撤幅度'
            },
            'performance_metrics': {
                'sharpe_ratio': f"{risk_metrics.sharpe_ratio:.2f}",
                'sortino_ratio': f"{risk_metrics.sortino_ratio:.2f}",
                'interpretation': '风险调整后收益指标'
            },
            'volatility_metrics': {
                'annual_volatility': f"{risk_metrics.volatility:.2%}",
                'daily_volatility': f"{risk_metrics.volatility / np.sqrt(252):.2%}",
                'interpretation': '价格波动程度'
            },
            'risk_level': self._assess_risk_level(risk_metrics)
        }
    
    def _format_alerts(self, alerts: List[RiskAlert]) -> Dict[str, Any]:
        """格式化风险警报"""
        if not alerts:
            return {'total': 0, 'by_severity': {}, 'recent': []}
        
        # 按严重程度分类
        alerts_by_severity = {}
        for alert in alerts:
            severity = alert.severity
            if severity not in alerts_by_severity:
                alerts_by_severity[severity] = []
            alerts_by_severity[severity].append(alert)
        
        # 最近警报（按时间排序）
        recent_alerts = sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:10]
        
        return {
            'total': len(alerts),
            'by_severity': {
                severity: len(alerts_list) 
                for severity, alerts_list in alerts_by_severity.items()
            },
            'summary': {
                'critical': len(alerts_by_severity.get('critical', [])),
                'high': len(alerts_by_severity.get('high', [])),
                'medium': len(alerts_by_severity.get('medium', [])),
                'low': len(alerts_by_severity.get('low', []))
            },
            'recent': [
                {
                    'timestamp': alert.timestamp.isoformat(),
                    'risk_type': alert.risk_type,
                    'severity': alert.severity,
                    'message': alert.message,
                    'symbol': alert.symbol,
                    'action_required': alert.action_required
                }
                for alert in recent_alerts
            ]
        }
    
    def _analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析组合风险"""
        if not portfolio_data:
            return {'analysis': 'No portfolio data available'}
        
        try:
            # 计算集中度
            total_value = sum(data.get('value', 0) for data in portfolio_data.values())
            
            if total_value > 0:
                concentration = {}
                for symbol, data in portfolio_data.items():
                    value = data.get('value', 0)
                    concentration[symbol] = value / total_value
                
                # 计算集中度指标
                herfindahl_index = sum(weight ** 2 for weight in concentration.values())
                max_concentration = max(concentration.values()) if concentration else 0
                
                return {
                    'total_value': total_value,
                    'concentration': concentration,
                    'risk_metrics': {
                        'herfindahl_index': herfindahl_index,
                        'max_concentration': max_concentration,
                        'diversification_score': 1 - herfindahl_index
                    },
                    'interpretation': {
                        'herfindahl_index': 'HHI指数，越接近1表示越集中',
                        'max_concentration': '最大单一资产占比',
                        'diversification_score': '多元化评分，越接近1表示越分散'
                    }
                }
            else:
                return {'analysis': 'Portfolio has zero value'}
                
        except Exception as e:
            logger.error(f"分析组合风险失败: {e}")
            return {'error': str(e)}
    
    def _assess_risk_level(self, risk_metrics: RiskMetrics) -> str:
        """评估风险等级"""
        if not risk_metrics:
            return 'Unknown'
        
        risk_score = 0
        
        # VaR评分
        if risk_metrics.var_95 > 0.05:
            risk_score += 3
        elif risk_metrics.var_95 > 0.03:
            risk_score += 2
        elif risk_metrics.var_95 > 0.01:
            risk_score += 1
        
        # 最大回撤评分
        if risk_metrics.max_drawdown > 0.2:
            risk_score += 3
        elif risk_metrics.max_drawdown > 0.15:
            risk_score += 2
        elif risk_metrics.max_drawdown > 0.1:
            risk_score += 1
        
        # 夏普比率评分（低夏普比率增加风险评分）
        if risk_metrics.sharpe_ratio < 0.5:
            risk_score += 3
        elif risk_metrics.sharpe_ratio < 1.0:
            risk_score += 2
        elif risk_metrics.sharpe_ratio < 1.5:
            risk_score += 1
        
        # 波动率评分
        if risk_metrics.volatility > 0.4:
            risk_score += 3
        elif risk_metrics.volatility > 0.3:
            risk_score += 2
        elif risk_metrics.volatility > 0.2:
            risk_score += 1
        
        # 确定风险等级
        if risk_score >= 9:
            return 'Extreme'
        elif risk_score >= 7:
            return 'High'
        elif risk_score >= 4:
            return 'Medium'
        elif risk_score >= 2:
            return 'Low'
        else:
            return 'Very Low'
    
    def _generate_recommendations(self, risk_metrics: RiskMetrics, 
                               alerts: List[RiskAlert]) -> List[Dict[str, Any]]:
        """生成风险建议"""
        recommendations = []
        
        try:
            # 基于VaR的建议
            if risk_metrics and risk_metrics.var_95 > 0.03:
                recommendations.append({
                    'type': 'position_management',
                    'priority': 'high',
                    'title': '降低组合风险敞口',
                    'description': f'当前95% VaR为{risk_metrics.var_95:.2%}，超过建议阈值3%',
                    'actions': [
                        '减少高风险资产配置',
                        '增加对冲工具使用',
                        '调整止损水平'
                    ]
                })
            
            # 基于最大回撤的建议
            if risk_metrics and risk_metrics.max_drawdown > 0.15:
                recommendations.append({
                    'type': 'drawdown_control',
                    'priority': 'critical',
                    'title': '控制最大回撤',
                    'description': f'当前最大回撤为{risk_metrics.max_drawdown:.2%}，超过安全阈值15%',
                    'actions': [
                        '立即评估投资策略',
                        '考虑减仓或止损',
                        '加强风险监控'
                    ]
                })
            
            # 基于夏普比率的建议
            if risk_metrics and risk_metrics.sharpe_ratio < 0.5:
                recommendations.append({
                    'type': 'performance_optimization',
                    'priority': 'medium',
                    'title': '优化风险调整后收益',
                    'description': f'夏普比率{risk_metrics.sharpe_ratio:.2f}偏低，需要改善风险收益比',
                    'actions': [
                        '优化资产配置',
                        '降低无效交易频率',
                        '改善持仓时间管理'
                    ]
                })
            
            # 基于警报的建议
            critical_alerts = [a for a in alerts if a.severity == 'critical']
            if critical_alerts:
                recommendations.append({
                    'type': 'alert_response',
                    'priority': 'critical',
                    'title': '立即处理关键风险警报',
                    'description': f'有{len(critical_alerts)}个关键风险警报需要处理',
                    'actions': [
                        '立即评估警报原因',
                        '执行应急止损措施',
                        '通知风险管理团队'
                    ]
                })
            
            # 基于波动率的建议
            if risk_metrics and risk_metrics.volatility > 0.3:
                recommendations.append({
                    'type': 'volatility_management',
                    'priority': 'medium',
                    'title': '管理高波动风险',
                    'description': f'年化波动率{risk_metrics.volatility:.2%}偏高',
                    'actions': [
                        '增加波动率对冲工具',
                        '降低仓位规模',
                        '缩短持仓时间'
                    ]
                })
            
        except Exception as e:
            logger.error(f"生成建议失败: {e}")
        
        return recommendations
    
    def _check_compliance(self, risk_metrics: RiskMetrics, 
                        alerts: List[RiskAlert]) -> Dict[str, Any]:
        """合规性检查"""
        compliance_status = {
            'overall': 'compliant',
            'checks': [],
            'violations': []
        }
        
        try:
            # 检查VaR限制
            if risk_metrics and risk_metrics.var_95 > 0.05:
                compliance_status['violations'].append({
                    'rule': 'VaR Limit',
                    'limit': '5%',
                    'actual': f'{risk_metrics.var_95:.2%}',
                    'status': 'exceeded'
                })
                compliance_status['overall'] = 'non_compliant'
            else:
                compliance_status['checks'].append({
                    'rule': 'VaR Limit',
                    'status': 'passed'
                })
            
            # 检查最大回撤限制
            if risk_metrics and risk_metrics.max_drawdown > 0.2:
                compliance_status['violations'].append({
                    'rule': 'Max Drawdown Limit',
                    'limit': '20%',
                    'actual': f'{risk_metrics.max_drawdown:.2%}',
                    'status': 'exceeded'
                })
                compliance_status['overall'] = 'non_compliant'
            else:
                compliance_status['checks'].append({
                    'rule': 'Max Drawdown Limit',
                    'status': 'passed'
                })
            
            # 检查关键警报数量
            critical_alerts = [a for a in alerts if a.severity == 'critical']
            if len(critical_alerts) > 0:
                compliance_status['violations'].append({
                    'rule': 'Critical Alert Limit',
                    'limit': '0',
                    'actual': f'{len(critical_alerts)}',
                    'status': 'exceeded'
                })
                compliance_status['overall'] = 'non_compliant'
            else:
                compliance_status['checks'].append({
                    'rule': 'Critical Alert Limit',
                    'status': 'passed'
                })
            
        except Exception as e:
            logger.error(f"合规性检查失败: {e}")
        
        return compliance_status
    
    def save_report(self, report: Dict[str, Any], filename: str = None) -> str:
        """保存报告到文件"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"risk_report_{timestamp}.json"
            
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"风险报告已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
            return ""
    
    def generate_summary_dashboard(self, report: Dict[str, Any]) -> str:
        """生成摘要仪表板HTML"""
        try:
            html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>风险管理仪表板</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric { display: inline-block; margin: 10px 20px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #333; }
        .metric-label { color: #666; margin-top: 5px; }
        .alert { padding: 10px; margin: 5px 0; border-radius: 5px; }
        .critical { background-color: #ffebee; color: #c62828; border-left: 4px solid #c62828; }
        .high { background-color: #fff3e0; color: #ef6c00; border-left: 4px solid #ef6c00; }
        .medium { background-color: #fff8e1; color: #f9a825; border-left: 4px solid #f9a825; }
        .low { background-color: #e8f5e8; color: #2e7d32; border-left: 4px solid #2e7d32; }
        .recommendation { background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .status-compliant { color: #4caf50; font-weight: bold; }
        .status-non-compliant { color: #f44336; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ AI量化交易系统 - 风险管理仪表板</h1>
            <p>报告生成时间: {report_time}</p>
        </div>
        
        <div class="card">
            <h2>📊 核心风险指标</h2>
            {metrics_html}
        </div>
        
        <div class="card">
            <h2>🚨 风险警报状态</h2>
            {alerts_html}
        </div>
        
        <div class="card">
            <h2>📋 合规性检查</h2>
            {compliance_html}
        </div>
        
        <div class="card">
            <h2>💡 风险管理建议</h2>
            {recommendations_html}
        </div>
    </div>
</body>
</html>
            """
            
            # 生成指标HTML
            metrics_html = self._generate_metrics_html(report.get('risk_metrics', {}))
            
            # 生成警报HTML
            alerts_html = self._generate_alerts_html(report.get('risk_alerts', {}))
            
            # 生成合规性HTML
            compliance_html = self._generate_compliance_html(report.get('compliance_check', {}))
            
            # 生成建议HTML
            recommendations_html = self._generate_recommendations_html(report.get('risk_recommendations', []))
            
            # 填充模板
            html_content = html_template.format(
                report_time=report.get('report_metadata', {}).get('generated_at', 'N/A'),
                metrics_html=metrics_html,
                alerts_html=alerts_html,
                compliance_html=compliance_html,
                recommendations_html=recommendations_html
            )
            
            # 保存HTML文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"risk_dashboard_{timestamp}.html"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"风险仪表板已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"生成仪表板失败: {e}")
            return ""
    
    def _generate_metrics_html(self, risk_metrics: Dict[str, Any]) -> str:
        """生成指标HTML"""
        if not risk_metrics:
            return "<p>暂无风险指标数据</p>"
        
        html = "<div style='display: flex; flex-wrap: wrap; justify-content: space-around;'>"
        
        # VaR指标
        var_data = risk_metrics.get('value_at_risk', {})
        html += f"""
        <div class="metric">
            <div class="metric-value">{var_data.get('var_95', 'N/A')}</div>
            <div class="metric-label">95% VaR</div>
        </div>
        <div class="metric">
            <div class="metric-value">{var_data.get('var_99', 'N/A')}</div>
            <div class="metric-label">99% VaR</div>
        </div>
        """
        
        # 回撤指标
        drawdown_data = risk_metrics.get('drawdown_metrics', {})
        html += f"""
        <div class="metric">
            <div class="metric-value">{drawdown_data.get('max_drawdown', 'N/A')}</div>
            <div class="metric-label">最大回撤</div>
        </div>
        """
        
        # 性能指标
        perf_data = risk_metrics.get('performance_metrics', {})
        html += f"""
        <div class="metric">
            <div class="metric-value">{perf_data.get('sharpe_ratio', 'N/A')}</div>
            <div class="metric-label">夏普比率</div>
        </div>
        <div class="metric">
            <div class="metric-value">{perf_data.get('sortino_ratio', 'N/A')}</div>
            <div class="metric-label">索提诺比率</div>
        </div>
        """
        
        # 波动率指标
        vol_data = risk_metrics.get('volatility_metrics', {})
        html += f"""
        <div class="metric">
            <div class="metric-value">{vol_data.get('annual_volatility', 'N/A')}</div>
            <div class="metric-label">年化波动率</div>
        </div>
        <div class="metric">
            <div class="metric-value" style="color: {'red' if risk_metrics.get('risk_level') in ['High', 'Extreme'] else 'green'};">{risk_metrics.get('risk_level', 'N/A')}</div>
            <div class="metric-label">风险等级</div>
        </div>
        """
        
        html += "</div>"
        return html
    
    def _generate_alerts_html(self, alerts_data: Dict[str, Any]) -> str:
        """生成警报HTML"""
        summary = alerts_data.get('summary', {})
        total = alerts_data.get('total', 0)
        
        html = f"<p>警报总数: <strong>{total}</strong></p>"
        
        if summary:
            html += "<div style='margin: 10px 0;'>"
            for severity, count in summary.items():
                severity_cn = {
                    'critical': '严重',
                    'high': '高',
                    'medium': '中等',
                    'low': '低'
                }.get(severity, severity)
                
                html += f"""
                <div class="alert {severity}">
                    {severity_cn}: {count} 个
                </div>
                """
            html += "</div>"
        
        return html
    
    def _generate_compliance_html(self, compliance_data: Dict[str, Any]) -> str:
        """生成就规性HTML"""
        overall_status = compliance_data.get('overall', 'compliant')
        status_class = 'status-compliant' if overall_status == 'compliant' else 'status-non-compliant'
        status_text = '合规' if overall_status == 'compliant' else '不合规'
        
        html = f"""
        <p>整体合规状态: <span class="{status_class}">{status_text}</span></p>
        """
        
        violations = compliance_data.get('violations', [])
        if violations:
            html += "<h4>合规违规:</h4>"
            for violation in violations:
                html += f"""
                <div class="alert high">
                    <strong>{violation.get('rule', 'N/A')}</strong>: 
                    实际值 {violation.get('actual', 'N/A')} 超过限制 {violation.get('limit', 'N/A')}
                </div>
                """
        else:
            html += "<p style='color: green;'>✅ 所有合规检查通过</p>"
        
        return html
    
    def _generate_recommendations_html(self, recommendations: List[Dict[str, Any]]) -> str:
        """生成建议HTML"""
        if not recommendations:
            return "<p>暂无特别建议</p>"
        
        html = ""
        for i, rec in enumerate(recommendations, 1):
            priority_emoji = {
                'critical': '🔴',
                'high': '🟠', 
                'medium': '🟡',
                'low': '🟢'
            }.get(rec.get('priority', 'low'), '⚪')
            
            html += f"""
            <div class="recommendation">
                <h4>{priority_emoji} {rec.get('title', f'建议 {i}')}</h4>
                <p>{rec.get('description', '')}</p>
                <ul>
            """
            
            for action in rec.get('actions', []):
                html += f"<li>{action}</li>"
            
            html += """
                </ul>
            </div>
            """
        
        return html


# 使用示例
def example_usage():
    """使用示例"""
    import json
    from datetime import datetime
    
    # 创建风险报告器
    reporter = RiskReporter()
    
    # 模拟风险指标
    risk_metrics = RiskMetrics(
        var_95=0.025,
        var_99=0.045,
        max_drawdown=0.12,
        sharpe_ratio=1.2,
        sortino_ratio=1.5,
        volatility=0.25,
        beta=1.1
    )
    
    # 模拟风险警报
    alerts = [
        RiskAlert(
            alert_id="alert_1",
            risk_type="position_size",
            severity="high",
            message="BTCUSDT仓位过大",
            timestamp=datetime.now(),
            symbol="BTCUSDT",
            value=0.12,
            threshold=0.1
        )
    ]
    
    # 模拟组合数据
    portfolio_data = {
        'BTCUSDT': {'value': 5000, 'weight': 0.5},
        'ETHUSDT': {'value': 3000, 'weight': 0.3},
        'BNBUSDT': {'value': 2000, 'weight': 0.2}
    }
    
    # 生成报告
    report = reporter.generate_risk_report(risk_metrics, alerts, portfolio_data)
    
    # 保存JSON报告
    json_file = reporter.save_report(report)
    print(f"JSON报告已保存: {json_file}")
    
    # 生成HTML仪表板
    html_file = reporter.generate_summary_dashboard(report)
    print(f"HTML仪表板已保存: {html_file}")
    
    # 打印报告摘要
    print("\n=== 风险报告摘要 ===")
    print(f"风险等级: {report.get('risk_metrics', {}).get('risk_level', 'Unknown')}")
    print(f"警报总数: {report.get('risk_alerts', {}).get('total', 0)}")
    print(f"合规状态: {report.get('compliance_check', {}).get('overall', 'Unknown')}")
    print(f"建议数量: {len(report.get('risk_recommendations', []))}")


if __name__ == "__main__":
    example_usage()