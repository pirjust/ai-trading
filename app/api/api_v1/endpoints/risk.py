"""
风险相关API端点
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List

from risk_management.risk_engine import RiskEngine

router = APIRouter()

# 全局风险引擎实例
risk_engine = RiskEngine()

@router.on_event("startup")
async def startup_event():
    """启动时初始化风险引擎"""
    await risk_engine.initialize()

@router.post("/check-trade")
async def check_trade_risk(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "market",
    account_id: int = None
) -> Dict:
    """检查交易风险"""
    try:
        result = await risk_engine.check_trade_risk(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            account_id=account_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险检查失败: {str(e)}")

@router.post("/monitor-portfolio")
async def monitor_portfolio_risk(portfolio: Dict[str, float]) -> Dict:
    """监控投资组合风险"""
    try:
        risk_metrics = await risk_engine.monitor_portfolio_risk(portfolio)
        return risk_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"组合风险监控失败: {str(e)}")

@router.get("/risk-report")
async def get_risk_report(portfolio: Dict[str, float]) -> Dict:
    """获取风险报告"""
    try:
        report = await risk_engine.get_risk_report(portfolio)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险报告生成失败: {str(e)}")

@router.get("/alerts")
async def get_active_alerts() -> List[Dict]:
    """获取当前活动警报"""
    try:
        alerts = [
            {
                "alert_id": alert.alert_id,
                "level": alert.level,
                "type": alert.type,
                "symbol": alert.symbol,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "value": alert.value,
                "threshold": alert.threshold
            }
            for alert in risk_engine.active_alerts
        ]
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取警报失败: {str(e)}")

@router.post("/calculate-var")
async def calculate_var(portfolio: Dict[str, float], confidence_level: float = 0.95) -> Dict:
    """计算风险价值(VaR)"""
    try:
        var = await risk_engine.calculate_var(portfolio, confidence_level)
        return {
            "var": var,
            "confidence_level": confidence_level,
            "portfolio_value": sum(portfolio.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VaR计算失败: {str(e)}")

@router.post("/calculate-es")
async def calculate_expected_shortfall(portfolio: Dict[str, float]) -> Dict:
    """计算预期亏损(ES)"""
    try:
        es = await risk_engine.calculate_expected_shortfall(portfolio)
        return {
            "expected_shortfall": es,
            "portfolio_value": sum(portfolio.values())
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ES计算失败: {str(e)}")

@router.get("/risk-history")
async def get_risk_history(limit: int = 100) -> List[Dict]:
    """获取风险历史记录"""
    try:
        history = risk_engine.risk_history[-limit:]
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取风险历史失败: {str(e)}")