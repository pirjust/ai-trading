#!/usr/bin/env python3
"""
AI量化交易系统备份脚本
用于定期备份数据库、配置文件和日志
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, backup_dir="/backup/ai-trading"):
        self.backup_dir = Path(backup_dir)
        self.project_root = Path("/www/wwwroot/ai-trading")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def ensure_backup_dir(self):
        """确保备份目录存在"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
            logger.info(f"创建备份目录: {self.backup_dir}")
    
    def backup_database(self):
        """备份数据库"""
        logger.info("开始备份数据库...")
        
        try:
            # PostgreSQL备份
            db_backup_file = self.backup_dir / f"ai_trading_db_{self.timestamp}.sql"
            
            cmd = [
                "pg_dump", "-h", "localhost", "-U", "ai_trader", 
                "-d", "ai_trading", "-f", str(db_backup_file)
            ]
            
            # 设置密码环境变量
            env = os.environ.copy()
            env["PGPASSWORD"] = "your_secure_password"  # 从环境变量获取
            
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"数据库备份完成: {db_backup_file}")
            return db_backup_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"数据库备份失败: {e}")
            return None
    
    def backup_config_files(self):
        """备份配置文件"""
        logger.info("开始备份配置文件...")
        
        config_backup_dir = self.backup_dir / f"config_{self.timestamp}"
        config_backup_dir.mkdir()
        
        # 需要备份的配置文件
        config_files = [
            ".env",
            "config/api_config.py",
            "config/trading_config.py", 
            "config/risk_config.py",
            "config/exchanges.py",
            "docker-compose.yml",
            "docker-compose.prod.yml",
            "Dockerfile",
            "requirements.txt",
            "pyproject.toml"
        ]
        
        for config_file in config_files:
            src = self.project_root / config_file
            if src.exists():
                dst = config_backup_dir / config_file
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        
        logger.info(f"配置文件备份完成: {config_backup_dir}")
        return config_backup_dir
    
    def backup_logs(self):
        """备份日志文件"""
        logger.info("开始备份日志文件...")
        
        logs_dir = self.project_root / "logs"
        if not logs_dir.exists():
            logger.warning("日志目录不存在，跳过备份")
            return None
        
        logs_backup_file = self.backup_dir / f"logs_{self.timestamp}.zip"
        
        with zipfile.ZipFile(logs_backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(logs_dir):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(logs_dir)
                    zipf.write(file_path, arcname)
        
        logger.info(f"日志文件备份完成: {logs_backup_file}")
        return logs_backup_file
    
    def backup_strategies(self):
        """备份策略文件"""
        logger.info("开始备份策略文件...")
        
        strategies_dir = self.project_root / "strategies"
        strategies_backup_file = self.backup_dir / f"strategies_{self.timestamp}.zip"
        
        with zipfile.ZipFile(strategies_backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(strategies_dir):
                for file in files:
                    if file.endswith('.py'):  # 只备份Python文件
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(strategies_dir)
                        zipf.write(file_path, arcname)
        
        logger.info(f"策略文件备份完成: {strategies_backup_file}")
        return strategies_backup_file
    
    def create_full_backup(self):
        """创建完整备份"""
        logger.info("🚀 开始创建完整备份")
        
        self.ensure_backup_dir()
        
        backup_files = []
        
        # 备份数据库
        db_file = self.backup_database()
        if db_file:
            backup_files.append(db_file)
        
        # 备份配置文件
        config_dir = self.backup_config_files()
        if config_dir:
            backup_files.append(config_dir)
        
        # 备份日志文件
        logs_file = self.backup_logs()
        if logs_file:
            backup_files.append(logs_file)
        
        # 备份策略文件
        strategies_file = self.backup_strategies()
        if strategies_file:
            backup_files.append(strategies_file)
        
        # 创建备份清单
        backup_list_file = self.backup_dir / f"backup_manifest_{self.timestamp}.txt"
        with open(backup_list_file, 'w') as f:
            f.write(f"备份时间: {datetime.now().isoformat()}\n")
            f.write("备份文件列表:\n")
            for backup_file in backup_files:
                f.write(f"- {backup_file}\n")
        
        logger.info(f"✅ 完整备份完成，共备份 {len(backup_files)} 个项目")
        return backup_files
    
    def cleanup_old_backups(self, keep_days=7):
        """清理旧备份文件"""
        logger.info("🧹 清理旧备份文件...")
        
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        deleted_count = 0
        for item in self.backup_dir.iterdir():
            if item.is_file() and item.stat().st_mtime < cutoff_time:
                item.unlink()
                deleted_count += 1
                logger.info(f"删除旧备份: {item.name}")
        
        logger.info(f"清理完成，共删除 {deleted_count} 个旧备份文件")
    
    def restore_backup(self, backup_date):
        """从备份恢复（需要手动实现）"""
        logger.info(f"开始从备份恢复: {backup_date}")
        
        # 这里需要根据备份文件实现具体的恢复逻辑
        # 包括数据库恢复、配置文件恢复等
        
        logger.warning("恢复功能需要手动实现，请谨慎操作")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python backup.py full        # 创建完整备份")
        print("  python backup.py cleanup     # 清理旧备份")
        print("  python backup.py restore <date> # 恢复备份")
        sys.exit(1)
    
    action = sys.argv[1]
    backup_manager = BackupManager()
    
    try:
        if action == "full":
            backup_manager.create_full_backup()
        elif action == "cleanup":
            backup_manager.cleanup_old_backups()
        elif action == "restore":
            if len(sys.argv) < 3:
                print("请指定要恢复的备份日期")
                sys.exit(1)
            backup_date = sys.argv[2]
            backup_manager.restore_backup(backup_date)
        else:
            print(f"未知操作: {action}")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"备份操作失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()