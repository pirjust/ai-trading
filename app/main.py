"""
AI量化交易系统主入口
"""
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import asyncio

from core.config import settings
from core.database import engine, Base
from app.api.api_v1.api import api_router
from risk_management.risk_monitor import get_risk_monitor
from risk_management.risk_reporter import get_risk_reporter, ReportType

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI量化加密货币交易系统",
    description="基于人工智能的自主进化量化交易平台",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# 全局风险监控器实例
risk_monitor = None
risk_reporter = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化风险监控"""
    global risk_monitor, risk_reporter
    try:
        risk_monitor = await get_risk_monitor()
        risk_reporter = await get_risk_reporter()
        await risk_monitor.start_monitoring()
        print("风险监控服务已启动")
        print("风险报告服务已初始化")
    except Exception as e:
        print(f"风险服务启动失败: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时停止风险监控"""
    global risk_monitor
    if risk_monitor:
        try:
            await risk_monitor.stop_monitoring()
            print("风险监控服务已停止")
        except Exception as e:
            print(f"风险监控服务停止失败: {str(e)}")

@app.get("/")
async def root():
    return {"message": "AI量化交易系统API服务"}

@app.get("/health")
async def health_check():
    global risk_monitor
    
    health_status = {
        "status": "healthy",
        "service": "ai-trading-api",
        "version": "1.0.0",
        "risk_monitor": "running" if risk_monitor and risk_monitor.is_running else "stopped"
    }
    
    if risk_monitor:
        try:
            monitoring_status = await risk_monitor.get_monitoring_status()
            health_status["monitoring_status"] = monitoring_status
        except Exception as e:
            health_status["monitoring_status"] = {"error": str(e)}
    
    return JSONResponse(content=health_status)

@app.get("/risk/status")
async def get_risk_status():
    """获取风险监控状态"""
    global risk_monitor
    
    if not risk_monitor:
        return JSONResponse(
            content={"error": "风险监控服务未初始化"},
            status_code=503
        )
    
    try:
        monitoring_status = await risk_monitor.get_monitoring_status()
        risk_summary = await risk_monitor.get_risk_summary()
        
        return {
            "monitoring_status": monitoring_status,
            "risk_summary": risk_summary
        }
    except Exception as e:
        return JSONResponse(
            content={"error": f"获取风险状态失败: {str(e)}"},
            status_code=500
        )

@app.post("/risk/control/start")
async def start_risk_monitoring():
    """启动风险监控"""
    global risk_monitor
    
    if not risk_monitor:
        return JSONResponse(
            content={"error": "风险监控服务未初始化"},
            status_code=503
        )
    
    try:
        if risk_monitor.is_running:
            return {"message": "风险监控已在运行中"}
        
        await risk_monitor.start_monitoring()
        return {"message": "风险监控已启动"}
    except Exception as e:
        return JSONResponse(
            content={"error": f"启动风险监控失败: {str(e)}"},
            status_code=500
        )

@app.post("/risk/control/stop")
async def stop_risk_monitoring():
    """停止风险监控"""
    global risk_monitor
    
    if not risk_monitor:
        return JSONResponse(
            content={"error": "风险监控服务未初始化"},
            status_code=503
        )
    
    try:
        if not risk_monitor.is_running:
            return {"message": "风险监控已停止"}
        
        await risk_monitor.stop_monitoring()
        return {"message": "风险监控已停止"}
    except Exception as e:
        return JSONResponse(
            content={"error": f"停止风险监控失败: {str(e)}"},
            status_code=500
        )

# 风险报告API端点
@app.get("/risk/reports/generate")
async def generate_risk_report(
    report_type: str = "daily",
    start_time: str = None,
    end_time: str = None
):
    """生成风险报告"""
    global risk_reporter
    
    if not risk_reporter:
        return JSONResponse(
            content={"error": "风险报告服务未初始化"},
            status_code=503
        )
    
    try:
        # 解析报告类型
        try:
            report_type_enum = ReportType(report_type)
        except ValueError:
            return JSONResponse(
                content={"error": f"无效的报告类型: {report_type}"},
                status_code=400
            )
        
        # 解析时间参数
        start_datetime = None
        end_datetime = None
        
        if start_time:
            try:
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    content={"error": "无效的开始时间格式"},
                    status_code=400
                )
        
        if end_time:
            try:
                end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    content={"error": "无效的结束时间格式"},
                    status_code=400
                )
        
        # 生成报告
        report = await risk_reporter.generate_report(
            report_type_enum,
            start_datetime,
            end_datetime
        )
        
        return {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "generated_at": report.generated_at.isoformat(),
            "active_alerts": report.active_alerts,
            "critical_alerts": report.critical_alerts,
            "recommendations": report.recommendations
        }
    except Exception as e:
        return JSONResponse(
            content={"error": f"生成风险报告失败: {str(e)}"},
            status_code=500
        )

@app.get("/risk/reports/{report_id}")
async def get_risk_report(report_id: str):
    """获取特定风险报告"""
    global risk_reporter
    
    if not risk_reporter:
        return JSONResponse(
            content={"error": "风险报告服务未初始化"},
            status_code=503
        )
    
    try:
        if report_id not in risk_reporter.reports:
            return JSONResponse(
                content={"error": "报告不存在"},
                status_code=404
            )
        
        report = risk_reporter.reports[report_id]
        
        # 转换为字典格式返回
        report_dict = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "generated_at": report.generated_at.isoformat(),
            "risk_metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "threshold": metric.threshold,
                    "status": metric.status,
                    "trend": metric.trend,
                    "description": metric.description
                }
                for metric in report.risk_metrics
            ],
            "portfolio_risk": {
                "portfolio_value": report.portfolio_risk.portfolio_value,
                "var_95": report.portfolio_risk.var_95,
                "var_99": report.portfolio_risk.var_99,
                "expected_shortfall": report.portfolio_risk.expected_shortfall,
                "concentration_risk": report.portfolio_risk.concentration_risk,
                "liquidity_risk": report.portfolio_risk.liquidity_risk,
                "max_drawdown": report.portfolio_risk.max_drawdown,
                "sharpe_ratio": report.portfolio_risk.sharpe_ratio
            },
            "position_risks": [
                {
                    "symbol": position.symbol,
                    "position_value": position.position_value,
                    "risk_score": position.risk_score,
                    "volatility": position.volatility,
                    "correlation": position.correlation,
                    "margin_usage": position.margin_usage
                }
                for position in report.position_risks
            ],
            "active_alerts": report.active_alerts,
            "critical_alerts": report.critical_alerts,
            "recommendations": report.recommendations,
            "monitoring_status": report.monitoring_status
        }
        
        return report_dict
    except Exception as e:
        return JSONResponse(
            content={"error": f"获取风险报告失败: {str(e)}"},
            status_code=500
        )

@app.get("/risk/reports/{report_id}/export")
async def export_risk_report(report_id: str, format: str = "json"):
    """导出风险报告"""
    global risk_reporter
    
    if not risk_reporter:
        return JSONResponse(
            content={"error": "风险报告服务未初始化"},
            status_code=503
        )
    
    try:
        if report_id not in risk_reporter.reports:
            return JSONResponse(
                content={"error": "报告不存在"},
                status_code=404
            )
        
        report = risk_reporter.reports[report_id]
        
        # 验证导出格式
        if format not in ["json", "csv", "html"]:
            return JSONResponse(
                content={"error": "不支持的导出格式"},
                status_code=400
            )
        
        # 导出报告
        exported_content = await risk_reporter.export_report(report, format)
        
        # 设置响应内容类型
        content_type = "application/json"
        if format == "csv":
            content_type = "text/csv"
        elif format == "html":
            content_type = "text/html"
        
        return JSONResponse(
            content={
                "report_id": report_id,
                "format": format,
                "content": exported_content,
                "content_type": content_type
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"导出风险报告失败: {str(e)}"},
            status_code=500
        )

@app.get("/risk/reports")
async def list_risk_reports(limit: int = 10, offset: int = 0):
    """列出所有风险报告"""
    global risk_reporter
    
    if not risk_reporter:
        return JSONResponse(
            content={"error": "风险报告服务未初始化"},
            status_code=503
        )
    
    try:
        reports = list(risk_reporter.reports.values())
        
        # 按生成时间排序
        reports.sort(key=lambda x: x.generated_at, reverse=True)
        
        # 分页
        paginated_reports = reports[offset:offset + limit]
        
        return {
            "total": len(reports),
            "limit": limit,
            "offset": offset,
            "reports": [
                {
                    "report_id": report.report_id,
                    "report_type": report.report_type.value,
                    "start_time": report.start_time.isoformat(),
                    "end_time": report.end_time.isoformat(),
                    "generated_at": report.generated_at.isoformat(),
                    "active_alerts": report.active_alerts,
                    "critical_alerts": report.critical_alerts
                }
                for report in paginated_reports
            ]
        }
    except Exception as e:
        return JSONResponse(
            content={"error": f"列出风险报告失败: {str(e)}"},
            status_code=500
        )

# 风险报告API端点
@app.get("/risk/reports/generate")
async def generate_risk_report(
    report_type: str = "daily",
    start_time: str = None,
    end_time: str = None
):
    """生成风险报告"""
    global risk_reporter
    
    if not risk_reporter:
        return JSONResponse(
            content={"error": "风险报告服务未初始化"},
            status_code=503
        )
    
    try:
        # 解析报告类型
        try:
            report_type_enum = ReportType(report_type)
        except ValueError:
            return JSONResponse(
                content={"error": f"无效的报告类型: {report_type}"},
                status_code=400
            )
        
        # 解析时间参数
        start_datetime = None
        end_datetime = None
        
        if start_time:
            try:
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    content={"error": "无效的开始时间格式"},
                    status_code=400
                )
        
        if end_time:
            try:
                end_datetime = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                return JSONResponse(
                    content={"error": "无效的结束时间格式"},
                    status_code=400
                )
        
        # 生成报告
        report = await risk_reporter.generate_report(
            report_type_enum,
            start_datetime,
            end_datetime
        )
        
        return {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "generated_at": report.generated_at.isoformat(),
            "active_alerts": report.active_alerts,
            "critical_alerts": report.critical_alerts,
            "recommendations": report.recommendations
        }
    except Exception as e:
        return JSONResponse(
            content={"error": f"生成风险报告失败: {str(e)}"},
            status_code=500
        )

@app.get("/risk/reports/{report_id}")
async def get_risk_report(report_id: str):
    """获取特定风险报告"""
    global risk_reporter
    
    if not risk_reporter:
        return JSONResponse(
            content={"error": "风险报告服务未初始化"},
            status_code=503
        )
    
    try:
        if report_id not in risk_reporter.reports:
            return JSONResponse(
                content={"error": "报告不存在"},
                status_code=404
            )
        
        report = risk_reporter.reports[report_id]
        
        # 转换为字典格式返回
        report_dict = {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "start_time": report.start_time.isoformat(),
            "end_time": report.end_time.isoformat(),
            "generated_at": report.generated_at.isoformat(),
            "risk_metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "threshold": metric.threshold,
                    "status": metric.status,
                    "trend": metric.trend,
                    "description": metric.description
                }
                for metric in report.risk_metrics
            ],
            "portfolio_risk": {
                "portfolio_value": report.portfolio_risk.portfolio_value,
                "var_95": report.portfolio_risk.var_95,
                "var_99": report.portfolio_risk.var_99,
                "expected_shortfall": report.portfolio_risk.expected_shortfall,
                "concentration_risk": report.portfolio_risk.concentration_risk,
                "liquidity_risk": report.portfolio_risk.liquidity_risk,
                "max_drawdown": report.portfolio_risk.max_drawdown,
                "sharpe_ratio": report.portfolio_risk.sharpe_ratio
            },
            "position_risks": [
                {
                    "symbol": position.symbol,
                    "position_value": position.position_value,
                    "risk_score": position.risk_score,
                    "volatility": position.volatility,
                    "correlation": position.correlation,
                    "margin_usage": position.margin_usage
                }
                for position in report.position_risks
            ],
            "active_alerts": report.active_alerts,
            "critical_alerts": report.critical_alerts,
            "recommendations": report.recommendations,
            "monitoring_status": report.monitoring_status
        }
        
        return report_dict
    except Exception as e:
        return JSONResponse(
            content={"error": f"获取风险报告失败: {str(e)}"},
            status_code=500
        )

@app.get("/risk/reports/{report_id}/export")
async def export_risk_report(report_id: str, format: str = "json"):
    """导出风险报告"""
    global risk_reporter
    
    if not risk_reporter:
        return JSONResponse(
            content={"error": "风险报告服务未初始化"},
            status_code=503
        )
    
    try:
        if report_id not in risk_reporter.reports:
            return JSONResponse(
                content={"error": "报告不存在"},
                status_code=404
            )
        
        report = risk_reporter.reports[report_id]
        
        # 验证导出格式
        if format not in ["json", "csv", "html"]:
            return JSONResponse(
                content={"error": "不支持的导出格式"},
                status_code=400
            )
        
        # 导出报告
        exported_content = await risk_reporter.export_report(report, format)
        
        # 设置响应内容类型
        content_type = "application/json"
        if format == "csv":
            content_type = "text/csv"
        elif format == "html":
            content_type = "text/html"
        
        return JSONResponse(
            content={
                "report_id": report_id,
                "format": format,
                "content": exported_content,
                "content_type": content_type
            }
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"导出风险报告失败: {str(e)}"},
            status_code=500
        )

@app.get("/risk/reports")
async def list_risk_reports(limit: int = 10, offset: int = 0):
    """列出所有风险报告"""
    global risk_reporter
    
    if not risk_reporter:
        return JSONResponse(
            content={"error": "风险报告服务未初始化"},
            status_code=503
        )
    
    try:
        reports = list(risk_reporter.reports.values())
        
        # 按生成时间排序
        reports.sort(key=lambda x: x.generated_at, reverse=True)
        
        # 分页
        paginated_reports = reports[offset:offset + limit]
        
        return {
            "total": len(reports),
            "limit": limit,
            "offset": offset,
            "reports": [
                {
                    "report_id": report.report_id,
                    "report_type": report.report_type.value,
                    "start_time": report.start_time.isoformat(),
                    "end_time": report.end_time.isoformat(),
                    "generated_at": report.generated_at.isoformat(),
                    "active_alerts": report.active_alerts,
                    "critical_alerts": report.critical_alerts
                }
                for report in paginated_reports
            ]
        }
    except Exception as e:
        return JSONResponse(
            content={"error": f"列出风险报告失败: {str(e)}"},
            status_code=500
        )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.WEB_HOST,
        port=settings.WEB_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )