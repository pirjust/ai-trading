#!/usr/bin/env python3
"""
AI量化交易系统部署脚本
用于在腾讯云宝塔面板上自动部署系统
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class DeploymentManager:
    def __init__(self, project_path):
        self.project_path = Path(project_path)
        self.bt_panel_path = Path("/www/wwwroot/ai-trading")
        
    def check_environment(self):
        """检查部署环境"""
        print("🔍 检查部署环境...")
        
        # 检查宝塔面板
        if not os.path.exists("/www/server/panel"):
            print("❌ 未检测到宝塔面板，请先安装宝塔面板")
            return False
        
        # 检查Docker
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            print("✅ Docker已安装")
        except:
            print("❌ Docker未安装，请先安装Docker")
            return False
            
        # 检查Python
        try:
            result = subprocess.run(["python3", "--version"], check=True, capture_output=True, text=True)
            print(f"✅ Python版本: {result.stdout.strip()}")
        except:
            print("❌ Python3未安装")
            return False
            
        return True
    
    def create_project_directory(self):
        """创建项目目录"""
        print("📁 创建项目目录...")
        
        if not self.bt_panel_path.exists():
            self.bt_panel_path.mkdir(parents=True)
            print(f"✅ 创建目录: {self.bt_panel_path}")
        else:
            print(f"✅ 目录已存在: {self.bt_panel_path}")
    
    def copy_project_files(self):
        """复制项目文件"""
        print("📂 复制项目文件...")
        
        # 需要复制的目录和文件
        items_to_copy = [
            "agents/", "app/", "config/", "core/", "data/", 
            "execution/", "monitoring/", "risk_management/", 
            "strategies/", "web_app/", "scripts/",
            "requirements.txt", "pyproject.toml", "Dockerfile",
            "docker-compose.yml", "docker-compose.prod.yml",
            ".env.example", "README.md"
        ]
        
        for item in items_to_copy:
            src = self.project_path / item.rstrip('/')
            dst = self.bt_panel_path / item.rstrip('/')
            
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"✅ 复制目录: {item}")
            elif src.is_file():
                shutil.copy2(src, dst)
                print(f"✅ 复制文件: {item}")
    
    def setup_frontend(self):
        """设置前端项目"""
        print("🌐 设置前端项目...")
        
        frontend_path = self.project_path / "frontend"
        frontend_dest = self.bt_panel_path / "frontend"
        
        if frontend_path.exists():
            shutil.copytree(frontend_path, frontend_dest, dirs_exist_ok=True)
            
            # 安装前端依赖
            os.chdir(frontend_dest)
            subprocess.run(["npm", "install"], check=True)
            print("✅ 前端依赖安装完成")
            
            # 构建前端项目
            subprocess.run(["npm", "run", "build"], check=True)
            print("✅ 前端项目构建完成")
            
            # 复制构建文件到web_app/static
            static_dir = self.bt_panel_path / "web_app" / "static"
            if static_dir.exists():
                shutil.rmtree(static_dir)
            shutil.copytree(frontend_dest / "dist", static_dir)
            print("✅ 前端文件部署完成")
    
    def setup_environment(self):
        """设置环境变量"""
        print("⚙️ 设置环境变量...")
        
        env_file = self.bt_panel_path / ".env"
        env_example = self.bt_panel_path / ".env.example"
        
        if not env_file.exists() and env_example.exists():
            shutil.copy2(env_example, env_file)
            print("✅ 环境变量文件已创建，请编辑 .env 文件配置实际参数")
    
    def setup_database(self):
        """设置数据库"""
        print("🗄️ 设置数据库...")
        
        # 检查PostgreSQL是否安装
        try:
            subprocess.run(["systemctl", "status", "postgresql"], check=True, capture_output=True)
            print("✅ PostgreSQL服务运行中")
        except:
            print("⚠️ PostgreSQL未安装，请通过宝塔面板安装")
            return
        
        # 初始化数据库
        init_script = self.bt_panel_path / "scripts" / "init_database.py"
        if init_script.exists():
            os.chdir(self.bt_panel_path)
            subprocess.run(["python3", str(init_script)], check=True)
            print("✅ 数据库初始化完成")
    
    def build_docker_images(self):
        """构建Docker镜像"""
        print("🐳 构建Docker镜像...")
        
        os.chdir(self.bt_panel_path)
        
        # 构建主镜像
        subprocess.run(["docker", "build", "-t", "ai-trading:latest", "."], check=True)
        print("✅ Docker镜像构建完成")
    
    def start_services(self):
        """启动服务"""
        print("🚀 启动服务...")
        
        os.chdir(self.bt_panel_path)
        
        # 停止现有服务
        subprocess.run(["docker-compose", "down"], capture_output=True)
        
        # 启动生产环境服务
        subprocess.run(["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d"], check=True)
        print("✅ 服务启动完成")
    
    def setup_nginx(self):
        """设置Nginx反向代理"""
        print("🌐 设置Nginx配置...")
        
        nginx_config = """
server {
    listen 80;
    server_name your-domain.com;
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location / {
        root /www/wwwroot/ai-trading/web_app/static;
        try_files $uri $uri/ /index.html;
    }
}
"""
        
        # 保存Nginx配置
        config_path = "/www/server/panel/vhost/nginx/ai-trading.conf"
        with open(config_path, 'w') as f:
            f.write(nginx_config)
        
        print("✅ Nginx配置已生成，请通过宝塔面板重启Nginx")
    
    def setup_pm2(self):
        """设置PM2进程管理"""
        print("🔄 设置PM2进程管理...")
        
        pm2_config = """
module.exports = {
  apps: [{
    name: 'ai-trading-web',
    script: 'python',
    args: 'web_app/main.py',
    cwd: '/www/wwwroot/ai-trading',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production'
    }
  }, {
    name: 'ai-trading-data',
    script: 'python',
    args: 'scripts/start_data_collection.py',
    cwd: '/www/wwwroot/ai-trading',
    instances: 1,
    autorestart: true,
    watch: false
  }]
}
"""
        
        config_path = self.bt_panel_path / "ecosystem.config.js"
        with open(config_path, 'w') as f:
            f.write(pm2_config)
        
        print("✅ PM2配置已生成，请手动启动PM2服务")
    
    def run_health_check(self):
        """运行健康检查"""
        print("🔍 运行健康检查...")
        
        import time
        import requests
        
        # 等待服务启动
        time.sleep(10)
        
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                print("✅ 服务健康检查通过")
                return True
            else:
                print(f"❌ 服务健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def deploy(self):
        """执行完整部署流程"""
        print("🚀 开始部署AI量化交易系统...")
        print("=" * 50)
        
        try:
            # 检查环境
            if not self.check_environment():
                print("❌ 环境检查失败，请先解决环境问题")
                return False
            
            # 创建目录
            self.create_project_directory()
            
            # 复制文件
            self.copy_project_files()
            
            # 设置前端
            self.setup_frontend()
            
            # 设置环境变量
            self.setup_environment()
            
            # 设置数据库
            self.setup_database()
            
            # 构建Docker镜像
            self.build_docker_images()
            
            # 启动服务
            self.start_services()
            
            # 设置Nginx
            self.setup_nginx()
            
            # 设置PM2
            self.setup_pm2()
            
            # 健康检查
            if self.run_health_check():
                print("=" * 50)
                print("🎉 AI量化交易系统部署完成！")
                print("📊 访问地址: http://your-domain.com")
                print("🔧 请通过宝塔面板完成以下配置:")
                print("  1. 配置SSL证书")
                print("  2. 重启Nginx服务")
                print("  3. 启动PM2服务")
                print("  4. 配置防火墙规则")
                return True
            else:
                print("❌ 部署完成但健康检查失败，请检查服务状态")
                return False
                
        except Exception as e:
            print(f"❌ 部署过程中出现错误: {e}")
            return False

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("使用方法: python deploy.py <项目路径>")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    if not os.path.exists(project_path):
        print(f"❌ 项目路径不存在: {project_path}")
        sys.exit(1)
    
    deployer = DeploymentManager(project_path)
    
    if deployer.deploy():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()