"""
Web应用主入口
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from core.config import settings

app = FastAPI(
    title="AI量化交易系统Web界面",
    description="基于React的现代化交易监控界面",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板配置
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index():
    """主页面"""
    return {"message": "AI量化交易系统Web界面"}

@app.get("/dashboard")
async def dashboard():
    """仪表盘页面"""
    return {"message": "交易监控仪表盘"}

@app.get("/strategies")
async def strategies():
    """策略管理页面"""
    return {"message": "策略管理界面"}

@app.get("/trading")
async def trading():
    """交易监控页面"""
    return {"message": "实时交易监控"}

@app.get("/risk")
async def risk():
    """风险管理页面"""
    return {"message": "风险控制面板"}

if __name__ == "__main__":
    uvicorn.run(
        "web_app.main:app",
        host=settings.WEB_HOST,
        port=settings.WEB_PORT,
        reload=settings.DEBUG
    )