#!/bin/bash
# ============================================================
# 华为硬服务器 (192.168.1.12) 后端部署脚本
# 创建分布式项目管理 + 自动启动 + F:/hermes 归档
# 前置条件：已连接到局域网，SSH 或物理访问
# ============================================================
set -e

echo "=== 准备工作 ==="
# 先尝试 SSH（局域网）
if ssh -o ConnectTimeout=5 root@192.168.1.12 "echo CONNECTED" 2>/dev/null; then
  SERVER="root@192.168.1.12"
  REMOTE_MODE="ssh"
else
  echo "⚠️ 无法通过 SSH 连接 192.168.1.12"
  echo "请在物理终端上运行本脚本，或配置网络后重试。"
  echo "以下是需要执行的命令清单："
  REMOTE_MODE="manual"
fi

if [ "$REMOTE_MODE" = "ssh" ]; then
  echo "=== 1. 创建 F:/hermes 目录 ==="
  ssh "$SERVER" bash -s << 'REMOTE'
    # CentOS 下使用 mount 或创建目录结构
    mkdir -p /mnt/hermes-archive
    # 如果 F 盘是 Windows 分区，先挂载
    if lsblk | grep -q sda; then
      mount /dev/sda1 /mnt/hermes-archive 2>/dev/null || true
    fi
    echo "Archive dir ready"
REMOTE

  echo "=== 2. 从本地同步项目文件到归档 ==="
  rsync -avz --progress ~/textbook-project/ "$SERVER":/mnt/hermes-archive/textbook-project/

  echo "=== 3. 安装后端服务 ==="
  ssh "$SERVER" bash -s << 'REMOTE'
    # 安装 Docker 和 Hermes Agent
    curl -fsSL https://get.docker.com | bash
    systemctl enable docker
    systemctl start docker
    
    # 安装 Hermes
    curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
    
    # 创建自动启动脚本
    cat > /etc/systemd/system/hermes-backend.service << 'SERVICE'
[Unit]
Description=Hermes Textbook Backend Server
After=network.target docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/mnt/hermes-archive/textbook-project
ExecStart=/root/.local/bin/hermes gateway run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE
    
    systemctl daemon-reload
    systemctl enable hermes-backend
    systemctl start hermes-backend
    echo "Backend service installed and running"
REMOTE

  echo "=== 4. 验证 ==="
  ssh "$SERVER" "hermes gateway status; docker ps"
fi

echo ""
echo "=== 手动执行清单（如 SSH 不可用）==="
cat << 'MANUAL'
在 192.168.1.12 物理终端上执行：

1. 创建 F:/hermes 目录
   mkdir -p /F/hermes
   
2. 从 Windows 本机复制项目
   将 C:\Users\DELL\textbook-project\ 复制到 F:\hermes\textbook-project\

3. 安装后端服务
   curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
   hermes gateway install
   hermes gateway start

4. 配置自动启动
   hermes gateway install  # 已回答 Y/Y/Y

5. 验证
   hermes gateway status
MANUAL
