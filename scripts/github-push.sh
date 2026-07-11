#!/bin/bash
# ============================================================
# 中医教材编写平台 - GitHub 一键推送脚本
# 使用前请在 GitHub 生成 Personal Access Token：
#   Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
#   勾选 repo, workflow, admin:public_key 权限
# ============================================================
cd ~/textbook-project

echo "=== 步骤1: 输入你的 GitHub Personal Access Token ==="
read -s -p "Token: " GITHUB_TOKEN
echo ""

# 创建仓库（用 Token）
echo "=== 步骤2: 创建 GitHub 仓库 ==="
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d '{"name":"tcm-textbook-series","description":"中医中药病证单位教材编写平台 - 8大院系120门学科","private":false}'

# 添加 SSH 公钥
echo ""
echo "=== 步骤3: 添加 SSH 公钥到 GitHub 账户 ==="
SSH_KEY=$(cat ~/.ssh/github_tcm.pub)
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/keys \
  -d "{\"title\":\"tcm-textbook-server\",\"key\":\"$SSH_KEY\"}"

# 设置 remote 并推送
echo ""
echo "=== 步骤4: 推送代码 ==="
git remote add origin git@github.com:beijingcdy/tcm-textbook-series.git
git push -u origin master

echo ""
echo "✅ 完成！访问 https://github.com/beijingcdy/tcm-textbook-series"
