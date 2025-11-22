#!/bin/bash
# 宝塔面板一键部署脚本
# 文件名：baota_oneclick_deploy.sh

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
    exit 1
}

# 检查root权限
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "请使用root权限运行此脚本"
    fi
}

# 系统检测
detect_os() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    log "检测到操作系统: $OS $VER"
    
    case $OS in
        *Ubuntu*|*Debian*)
            OS_TYPE="debian"
            ;;
        *CentOS*|*RedHat*|*Fedora*)
            OS_TYPE="centos"
            ;;
        *)
            error "不支持的操作系统: $OS"
            ;;
    esac
}

# 安装宝塔面板
install_baota() {
    log "开始安装宝塔面板..."
    
    case $OS_TYPE in
        "debian")
            wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh
            bash install.sh ed8484bec
            ;;
        "centos")
            yum install -y wget
            wget -O install.sh https://download.bt.cn/install/install_6.0.sh
            bash install.sh
            ;;
    esac
    
    if [[ $? -eq 0 ]]; then
        log "宝塔面板安装完成"
        
        # 保存面板信息
        cat > /root/baota_info.txt << EOF
宝塔面板安装信息：
面板地址: http://$(hostname -I | awk '{print $1}'):8888
用户名: 安装脚本输出的用户名
密码: 安装脚本输出的密码
EOF
        
        cat /root/baota_info.txt
    else
        error "宝塔面板安装失败"
    fi
}

# 安装必要软件
install_software() {
    log "开始安装必要软件..."
    
    case $OS_TYPE in
        "debian")
            apt update
            apt install -y curl wget git vim htop unzip \
                software-properties-common apt-transport-https \
                ca-certificates gnupg lsb-release
            ;;
        "centos")
            yum update -y
            yum install -y curl wget git vim htop unzip \
                epel-release yum-utils
            ;;
    esac
}

# 配置防火墙
setup_firewall() {
    log "配置防火墙..."
    
    case $OS_TYPE in
        "debian")
            apt install -y ufw
            ufw --force enable
            ufw default deny incoming
            ufw default allow outgoing
            ufw allow 22/tcp
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw allow 8888/tcp
            ufw allow 5432/tcp
            ufw allow 6379/tcp
            ufw allow 8000/tcp
            ;;
        "centos")
            systemctl start firewalld
            systemctl enable firewalld
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --permanent --add-service=http
            firewall-cmd --permanent --add-service=https
            firewall-cmd --permanent --add-port=8888/tcp
            firewall-cmd --permanent --add-port=5432/tcp
            firewall-cmd --permanent --add-port=6379/tcp
            firewall-cmd --permanent --add-port=8000/tcp
            firewall-cmd --reload
            ;;
    esac
}

# 安装Python环境
install_python() {
    log "安装Python环境..."
    
    case $OS_TYPE in
        "debian")
            apt install -y python3 python3-pip python3-venv python3-dev
            ;;
        "centos")
            yum install -y python3 python3-pip python3-devel
            ;;
    esac
    
    # 创建虚拟环境
    python3 -m venv /opt/ai-trading
    source /opt/ai-trading/bin/activate
    
    # 升级pip
    pip install --upgrade pip setuptools wheel
}

# 安装系统依赖
install_dependencies() {
    log "安装系统依赖..."
    
    case $OS_TYPE in
        "debian")
            apt install -y \
                libpq-dev libssl-dev libffi-dev \
                libxml2-dev libxslt1-dev \
                libjpeg-dev libpng-dev libfreetype6-dev \
                zlib1g-dev libhdf5-dev \
                libblas-dev liblapack-dev gfortran
            ;;
        "centos")
            yum install -y \
                postgresql-devel openssl-devel libffi-devel \
                libxml2-devel libxslt-devel \
                libjpeg-turbo-devel libpng-devel freetype-devel \
                zlib-devel hdf5-devel \
                blas-devel lapack-devel gcc-gfortran
            ;;
    esac
}

# 安装数据库客户端
install_db_clients() {
    log "安装数据库客户端..."
    
    case $OS_TYPE in
        "debian")
            apt install -y postgresql-client redis-tools mysql-client
            ;;
        "centos")
            yum install -y postgresql redis mysql
            ;;
    esac
}

# 生成部署报告
generate_report() {
    log "生成部署报告..."
    
    cat > /root/deployment_report.txt << EOF
==========================================
宝塔面板一键部署报告
部署时间: $(date)
服务器IP: $(hostname -I | awk '{print $1}')
操作系统: $OS $VER
==========================================

✅ 已完成安装：
- 宝塔面板
- 基础工具
- Python环境
- 系统依赖
- 数据库客户端

📋 下一步操作：
1. 访问宝塔面板: http://$(hostname -I | awk '{print $1}'):8888
2. 在宝塔面板中安装以下软件：
   - Nginx 1.20+
   - PostgreSQL 13+
   - Redis 6.0+
   - Python项目管理器
3. 上传AI交易系统代码
4. 配置数据库和API接口

🔧 技术信息：
- Python虚拟环境: /opt/ai-trading
- 数据库端口: PostgreSQL(5432), Redis(6379)
- API服务端口: 8000

📞 技术支持：
- 查看日志: /var/log/
- 重启服务: systemctl restart service_name
- 防火墙状态: ufw status 或 firewall-cmd --state

EOF
    
    cat /root/deployment_report.txt
}

# 主函数
main() {
    log "开始宝塔面板一键部署..."
    
    check_root
    detect_os
    install_software
    setup_firewall
    install_baota
    install_python
    install_dependencies
    install_db_clients
    generate_report
    
    log "宝塔面板一键部署完成！"
    log "请查看 /root/deployment_report.txt 获取详细信息"
}

# 执行主函数
main "$@"