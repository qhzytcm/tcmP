# 华为云服务器部署指南
## 114.115.211.254 → Hermes Agent + Git + 教材看板前端

> **服务器环境**：CentOS 7.6.1810 (EOL) · 16vCPU · 62GB RAM · 40GB磁盘(94%满)
> **前置条件**：已通过 SSH 登录 `root@114.115.211.254`

---

## 阶段一：磁盘清理与系统准备

> ⚠️ **当前磁盘使用率 94%（仅剩 2.5GB）**，必须先清理。

### 步骤 1.1 — 检查磁盘占用详情

```bash
# 查看各目录占用
du -sh /* 2>/dev/null | sort -rh | head -15

# 查看大文件
find /var -type f -size +100M -exec ls -lh {} \; 2>/dev/null
find /tmp -type f -size +50M -exec ls -lh {} \; 2>/dev/null

# 查看 Docker 占用（如已安装）
docker system df 2>/dev/null
```

### 步骤 1.2 — 清理常见占用

```bash
# 清理 yum 缓存（通常可释放 500MB-2GB）
yum clean all
rm -rf /var/cache/yum/*

# 清理旧内核（保留当前使用的）
package-cleanup --oldkernels --count=1 -y 2>/dev/null || true

# 清理 journal 日志（保留最近 3 天）
journalctl --vacuum-time=3d 2>/dev/null || true

# 清理临时文件
rm -rf /tmp/*.log /tmp/*.tar /tmp/*.gz 2>/dev/null

# 清理 Docker 无用数据（如已安装）
docker system prune -af --volumes 2>/dev/null

# 检查清理后空间
df -h /
```

> **目标**：清理后可用空间 ≥ 5GB（理想 10GB+）

### 步骤 1.3 — 配置 CentOS 7 EOL 仓库

> CentOS 7 已于 2024年6月 EOL，需切换到 vault.epel.cloud 镜像：

```bash
# 备份原 repo 配置
mkdir -p /etc/yum.repos.d/backup
mv /etc/yum.repos.d/CentOS-*.repo /etc/yum.repos.d/backup/ 2>/dev/null

# 使用 vault 镜像
curl -o /etc/yum.repos.d/CentOS-Base.repo \
  https://mirrors.aliyun.com/repo/Centos-7.repo

# 如果阿里云镜像不可用，使用官方 vault
# curl -o /etc/yum.repos.d/CentOS-Base.repo \
#   https://raw.githubusercontent.com/beijingcdy/centos7-vault-repo/main/CentOS-Vault.repo

# 更新缓存
yum clean all && yum makecache fast
```

---

## 阶段二：安装最新版 Git

### 步骤 2.1 — 通过 IUS 仓库安装最新 Git

> CentOS 7 自带 git 1.8.x，IUS 仓库提供 git 2.x：

```bash
# 安装 IUS 仓库
yum install -y https://repo.ius.io/ius-release-el7.rpm

# 安装最新版 git（替换系统 git）
yum install -y git236 --replacepkgs

# 验证
git --version
# 期望输出：git version 2.36.x
```

### 步骤 2.2 — 配置 Git（备用：源码编译安装）

> 如果 IUS 仓库不可用，采用源码编译：

```bash
# 安装编译依赖
yum install -y make gcc curl-devel expat-devel gettext-devel \
  openssl-devel perl-devel zlib-devel autoconf asciidoc xmlto docbook2X

# 下载最新 Git 源码
cd /usr/local/src
curl -L -o git.tgz https://www.kernel.org/pub/software/scm/git/git-2.45.0.tar.gz
tar xzf git.tgz && cd git-2.45.0

# 编译安装
make configure
./configure --prefix=/usr/local
make -j$(nproc) all
make install

# 配置 PATH
echo 'export PATH=/usr/local/bin:$PATH' > /etc/profile.d/git.sh
source /etc/profile.d/git.sh

# 验证
/usr/local/bin/git --version
```

### 步骤 2.3 — 配置 Git 全局设置

```bash
git config --global user.name "beijingcdy"
git config --global user.email "beijingcdy@yeah.yeah"
git config --global core.autocrlf input
git config --global credential.helper store

# 克隆教材项目仓库
cd /opt
git clone https://github.com/beijingcdy/tcm-textbook-series.git
# 如果尚未推送，用本地 rsync：
# rsync -avz --progress root@YOUR_WINDOWS_IP:~/textbook-project/ /opt/tcm-textbook-series/
```

---

## 阶段三：安装 Hermes Agent

### 步骤 3.1 — 安装基础依赖

```bash
# Python 3.9 已预装，安装 pip 和 venv
yum install -y python3-pip python3-devel

# 安装编译工具（Hermes 部分依赖需要）
yum groupinstall -y "Development Tools"

# 升级 pip
pip3 install --upgrade pip setuptools wheel
```

### 步骤 3.2 — 安装 Hermes Agent

```bash
# 方案 A：一键安装脚本（推荐）
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# 安装后确保 hermes 在 PATH 中
source ~/.bashrc
hermes --version
```

### 步骤 3.3 — 如果一键安装失败，手动安装

```bash
# 方案 B：pip 安装
pip3 install hermes-agent

# 或从源码安装
git clone https://github.com/NousResearch/hermes-agent.git /opt/hermes-agent
cd /opt/hermes-agent
pip3 install -e .
```

### 步骤 3.4 — 初始化 Hermes

```bash
# 启动配置向导
hermes setup

# 或使用环境变量快速配置
hermes config set model.provider deepseek
hermes config set model.default deepseek-v4-flash
hermes config set DEEPSEEK_API_KEY "your-deepseek-key"

# 验证
hermes doctor
hermes config check
```

---

## 阶段四：部署看板前端（Nginx + HTTPS）

### 步骤 4.1 — 检查已有 Nginx

```bash
# 服务器已有 Nginx（端口 10001、8001）
nginx -v
ls /etc/nginx/conf.d/
```

### 步骤 4.2 — 配置看板站点

```bash
# 创建看板目录
mkdir -p /var/www/tcm-dashboard

# 从本机同步看板文件（在 Windows 本机执行）
# rsync -avz --progress ~/textbook-project/dashboard/ root@114.115.211.254:/var/www/tcm-dashboard/
# 或解压
# scp ~/path/to/dashboard.tar.gz root@114.115.211.254:/tmp/
# ssh root@114.115.211.254 "tar xzf /tmp/dashboard.tar.gz -C /var/www/tcm-dashboard/"
```

### 步骤 4.3 — 创建 Nginx 配置

```bash
cat > /etc/nginx/conf.d/tcm-dashboard.conf << 'NGINX'
server {
    listen 443 ssl http2;
    server_name _;

    # SSL 证书（如已有）
    # ssl_certificate /etc/nginx/ssl/fullchain.pem;
    # ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # 看板前端
    root /var/www/tcm-dashboard;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 项目评价接口（project-evaluation）
    location /api/evaluation/ {
        proxy_pass http://127.0.0.1:8642;
        proxy_set_header Host $host;
    }
}

server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}
NGINX

# 检查配置
nginx -t

# 重载 Nginx
systemctl reload nginx
```

### 步骤 4.4 — HTTPS 证书（如已有域名）

```bash
# 安装 certbot
yum install -y certbot python3-certbot-nginx

# 申请证书（将 example.com 替换为实际域名）
certbot --nginx -d example.com --non-interactive --agree-tos -m admin@example.com

# 自动续期
echo "0 3 * * * /usr/bin/certbot renew --quiet" >> /var/spool/cron/root
```

---

## 阶段五：启动 Hermes Gateway（常驻运行）

### 步骤 5.1 — 安装 Gateway 服务

> Hermes Gateway 作为 systemd 服务常驻运行：

```bash
# 创建 systemd 服务
cat > /etc/systemd/system/hermes-gateway.service << 'SERVICE'
[Unit]
Description=Hermes Agent Gateway - TCM Textbook Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tcm-textbook-series
ExecStart=$(which hermes) gateway run
Restart=always
RestartSec=10
Environment=HERMES_HOME=/root/.hermes
Environment=PYTHONIOENCODING=utf-8

[Install]
WantedBy=multi-user.target
SERVICE

# 启用并启动
systemctl daemon-reload
systemctl enable hermes-gateway
systemctl start hermes-gateway

# 验证
systemctl status hermes-gateway
```

### 步骤 5.2 — 启用 API Server

```bash
# 配置 API Server
hermes config set API_SERVER_ENABLED true
hermes config set API_SERVER_PORT 8642
hermes config set API_SERVER_KEY "textbook-platform-gateway-2026"

# 重启 gateway
systemctl restart hermes-gateway

# 验证
curl http://127.0.0.1:8642/health
curl -H "Authorization: Bearer textbook-platform-gateway-2026" http://127.0.0.1:8642/v1/models
```

### 步骤 5.3 — 安装 Kanban 看板服务

```bash
# 创建看板 HTTP 服务
cat > /etc/systemd/system/tcm-dashboard.service << 'SERVICE'
[Unit]
Description=TCM Textbook Dashboard Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tcm-textbook-series
ExecStart=/usr/bin/python3 -m http.server 8000 --directory /var/www/tcm-dashboard
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable tcm-dashboard
systemctl start tcm-dashboard

# 验证
curl http://127.0.0.1:8000/index.html | head -5
```

---

## 阶段六：验证全链路

### 步骤 6.1 — 从外部访问

```bash
# 在本地浏览器或 curl 验证
curl -k https://114.115.211.254           # 看板前端
curl http://114.115.211.254:8642/health    # Hermes API
curl http://114.115.211.254:8000           # 看板（备选）
```

### 步骤 6.2 — 验证 Git 版本管理

```bash
cd /opt/tcm-textbook-series
git log --oneline -5
git status
```

### 步骤 6.3 — 验证 Hermes 可用性

```bash
hermes doctor
hermes gateway status
hermes kanban boards list
```

---

## 附录 A：CentOS 7 EOL 常见问题

| 问题 | 解决方案 |
|:----|:---------|
| `yum install` 返回 404 | 使用 vault 镜像：`sed -i 's/mirror.centos.org/vault.centos.org/g' /etc/yum.repos.d/*.repo` |
| EPEL 仓库失效 | `yum install -y https://archives.fedoraproject.org/pub/archive/epel/7/x86_64/Packages/e/epel-release-7-14.noarch.rpm` |
| SSL 证书过期 | `yum update -y ca-certificates nss` |
| Python 版本过低 | 系统已预装 Python 3.9.13，满足要求 |

## 附录 B：故障排查

```bash
# Gateway 启动失败
hermes doctor --fix
journalctl -u hermes-gateway -n 50 --no-pager

# API Server 无响应
ss -tlnp | grep 8642
curl -v http://127.0.0.1:8642/health

# Nginx 问题
nginx -t
tail -50 /var/log/nginx/error.log

# 磁盘空间不足
du -sh /var/log/* | sort -rh | head -10
find / -type f -size +200M -exec ls -lh {} \; 2>/dev/null
```

---

> **编写日期**：2026-07-11
> **适用系统**：CentOS 7.6 x86_64
> **目标软件**：Git 2.36+ · Hermes Agent · Nginx · systemd
