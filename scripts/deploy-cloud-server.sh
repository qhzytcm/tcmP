#!/bin/bash
# ============================================================
# 华为云服务器 (114.115.211.254) 一键部署脚本
# 部署：看板前端 + Nginx HTTPS + 域名映射
# 前置条件：root 密码或 SSH 密钥已配置
# ============================================================
set -e

SERVER="root@114.115.211.254"
DOMAIN="tcm-textbook.example.com"  # 替换为你的域名

echo "=== 1. 安装基础软件 ==="
ssh "$SERVER" bash -s << 'REMOTE'
  yum install -y nginx certbot python3-certbot-nginx git nodejs
  systemctl enable nginx
  systemctl start nginx
  echo "Nginx installed"
REMOTE

echo "=== 2. 部署看板前端 ==="
# 从本地打包 dashboard
cd ~/textbook-project
tar czf /tmp/dashboard.tar.gz dashboard/
scp /tmp/dashboard.tar.gz "$SERVER":/tmp/
ssh "$SERVER" bash -s << 'REMOTE'
  mkdir -p /var/www/tcm-dashboard
  tar xzf /tmp/dashboard.tar.gz -C /var/www/tcm-dashboard/
  echo "Dashboard deployed to /var/www/tcm-dashboard/dashboard/"
REMOTE

echo "=== 3. 配置 Nginx ==="
ssh "$SERVER" bash -s << 'REMOTE'
cat > /etc/nginx/conf.d/tcm-dashboard.conf << 'NGINX'
server {
    listen 80;
    server_name _;

    # 看板前端
    location / {
        root /var/www/tcm-dashboard/dashboard;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # Hermes API 反向代理
    location /api/kanban/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /hermes-api/ {
        proxy_pass http://127.0.0.1:8642/;
        proxy_set_header Host $host;
        proxy_set_header Authorization "Bearer textbook-platform-gateway-2026";
    }
}
NGINX
  nginx -t && systemctl reload nginx
  echo "Nginx configured"
REMOTE

echo "=== 4. HTTPS 证书（如有域名）==="
echo "certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN"

echo ""
echo "✅ 部署完成！访问: http://114.115.211.254"
echo "   HTTPS: certbot 完成证书后 https://$DOMAIN"
