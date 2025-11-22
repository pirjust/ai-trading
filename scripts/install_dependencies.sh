#!/bin/bash

# AI量化交易系统依赖安装脚本
# 适用于宝塔面板部署

echo "开始安装AI量化交易系统依赖..."

# 检查Python版本
python3 --version

# 安装Python依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 安装前端依赖
echo "安装前端依赖..."
cd frontend
npm install
npm run build
cd ..

# 创建必要目录
echo "创建数据目录..."
mkdir -p data/logs
echo "创建数据库目录..."
mkdir -p data/db
echo "创建配置文件目录..."
mkdir -p config/production

# 设置权限
echo "设置文件权限..."
chmod +x scripts/*.py
chmod +x scripts/*.sh

# 初始化数据库
echo "初始化数据库..."
python scripts/init_database.py

echo "依赖安装完成！"
echo "请配置环境变量文件 .env"
echo "然后运行: python scripts/start_data_collection.py"