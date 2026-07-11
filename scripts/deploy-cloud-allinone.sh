#!/bin/bash
# ============================================================
# 华为云服务器 114.115.211.254 一键部署
# 安装：Git 最新版 + Hermes Agent + Nginx 看板前端
# 使用：ssh root@114.115.211.254 'bash -s' < deploy-cloud-allinone.sh
# ============================================================
set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║  华为云 · 教材平台一键部署                          ║"
echo "║  114.115.211.254 | CentOS 7.6 | 16vCPU 62GB       ║"
echo "╚════════════════════════════════════════════════════╝"

# ── 阶段1：磁盘清理 ──
echo ""
echo "═══ 阶段1：磁盘清理 ═══"
yum clean all 2>/dev/null
rm -rf /var/cache/yum/* 2>/dev/null
journalctl --vacuum-time=3d 2>/dev/null || true
docker system prune -af 2>/dev/null || true
echo "磁盘 $(df -h / | tail -1 | awk '{print $5}') → 清理完成"

# ── 阶段2：CentOS 7 EOL 仓库 ──
echo ""
echo "═══ 阶段2：配置 Yum 仓库 ═══"
if ! curl -sI https://mirrors.aliyun.com/repo/ &>/dev/null; then
  # vault 镜像
  sed -i 's|mirror.centos.org|vault.centos.org|g' /etc/yum.repos.d/*.repo
  sed -i 's|#baseurl|baseurl|g' /etc/yum.repos.d/*.repo
  sed -i 's|mirrorlist|#mirrorlist|g' /etc/yum.repos.d/*.repo
fi
yum makecache fast 2>/dev/null || yum makecache 2>/dev/null

# ── 阶段3：Git 最新版 ──
echo ""
echo "═══ 阶段3：安装 Git 最新版 ═══"
if git --version 2>/dev/null | grep -q "2."; then
  echo "Git $(git --version) 已安装，跳过"
else
  # 尝试 IUS 仓库
  yum install -y https://repo.ius.io/ius-release-el7.rpm 2>/dev/null && \
  yum install -y git236 --replacepkgs 2>/dev/null && \
  echo "Git $(git --version) 安装成功" || {
    echo "IUS 仓库不可用，源码编译..."
    yum groupinstall -y "Development Tools"
    yum install -y curl-devel expat-devel gettext-devel openssl-devel perl-devel zlib-devel
    cd /usr/local/src
    curl -L -o git.tgz https://www.kernel.org/pub/software/scm/git/git-2.45.0.tar.gz
    tar xzf git.tgz && cd git-2.45.0
    make configure && ./configure --prefix=/usr/local
    make -j$(nproc) && make install
    echo 'export PATH=/usr/local/bin:$PATH' > /etc/profile.d/git.sh
    source /etc/profile.d/git.sh
    echo "Git $(/usr/local/bin/git --version) 编译安装成功"
  }
fi

# Git 全局配置
git config --global user.name "beijingcdy"
git config --global user.email "beijingcdy@yeah.yeah"
git config --global core.autocrlf input

# ── 阶段4：Hermes Agent ──
echo ""
echo "═══ 阶段4：安装 Hermes Agent ═══"
if hermes --version 2>/dev/null; then
  echo "Hermes 已安装，跳过"
else
  # 安装依赖
  yum install -y python3-pip python3-devel
  pip3 install --upgrade pip setuptools wheel
  
  # 一键安装
  echo "正在下载安装 Hermes Agent..."
  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
  
  # 如果一键安装失败，回退到 pip
  if ! hermes --version 2>/dev/null; then
    pip3 install hermes-agent
  fi
  
  # 配置 PATH
  export PATH="$HOME/.local/bin:$PATH"
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
  source ~/.bashrc
  
  echo "Hermes $(hermes --version) 安装成功"
fi

# 配置 API Server
hermes config set API_SERVER_ENABLED true 2>/dev/null
hermes config set API_SERVER_PORT 8642 2>/dev/null
hermes config set API_SERVER_KEY "textbook-platform-gateway-2026" 2>/dev/null

# ── 阶段5：Nginx + 看板 ──
echo ""
echo "═══ 阶段5：部署看板前端 ═══"
if ! nginx -v 2>/dev/null; then
  yum install -y nginx
  systemctl enable nginx
fi

# 创建看板目录
mkdir -p /var/www/tcm-dashboard

# 创建 Nginx 配置
cat > /etc/nginx/conf.d/tcm-dashboard.conf << 'CONF'
server {
    listen 80;
    server_name _;
    
    root /var/www/tcm-dashboard;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host $host;
    }
}
CONF

nginx -t && systemctl reload nginx
echo "Nginx 配置完成"

# ── 阶段6：系统服务 ──
echo ""
echo "═══ 阶段6：注册系统服务 ═══"

cat > /etc/systemd/system/hermes-gateway.service << 'SVC1'
[Unit]
Description=Hermes Gateway - TCM Textbook Platform
After=network.target

[Service]
Type=simple
User=root
ExecStart=/root/.local/bin/hermes gateway run
Restart=always
RestartSec=10
Environment=PYTHONIOENCODING=utf-8

[Install]
WantedBy=multi-user.target
SVC1

systemctl daemon-reload
systemctl enable hermes-gateway
systemctl start hermes-gateway || echo "⚠️ Gateway 启动稍后验证"

# ── 阶段7：验证 ──
echo ""
echo "═══ 阶段7：部署验证 ═══"
echo ""
echo "✅ Git:      $(git --version 2>/dev/null || echo 'FAIL')"
echo "✅ Hermes:   $(hermes --version 2>/dev/null || echo 'check PATH')"
echo "✅ Nginx:    $(nginx -v 2>&1 || echo 'FAIL')"
echo "✅ Python:   $(python3 --version 2>/dev/null || echo 'FAIL')"
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║  部署完成！                                       ║"
echo "║                                                     ║"
echo "║  访问地址：                                        ║"
echo "║    http://114.115.211.254      看板前端             ║"
echo "║    http://114.115.211.254:8642  Hermes API          ║"
echo "║                                                     ║"
echo "║  后续操作：                                        ║"
echo "║  1. 从 Windows 本机同步看板文件                     ║"
echo "║     scp -r dashboard/* root@114.115.211.254:...     ║"
echo "║  2. 配置 HTTPS 证书（certbot --nginx）              ║"
echo "║  3. hermes gateway status 验证                     ║"
echo "╚════════════════════════════════════════════════════╝"
