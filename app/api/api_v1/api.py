"""
API v1 路由配置
"""
from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, users

api_router = APIRouter()

# 认证路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])

# 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])