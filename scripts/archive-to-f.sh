#!/bin/bash
# ============================================================
# 文件归档到华为硬服务器 F:/hermes
# 名称：中医教材编写平台的文档
# 使用: bash scripts/archive-to-f.sh
# ============================================================
set -e

ARCHIVE_DIR="/f/hermes"
LOCAL_DIR="$HOME/textbook-project"
DATE_TAG=$(date +%Y%m%d)

echo "=== 归档到 F:/hermes ==="

# 创建 F 盘目录（Windows 路径）
mkdir -p "$ARCHIVE_DIR/docs"
mkdir -p "$ARCHIVE_DIR/domain-specs"
mkdir -p "$ARCHIVE_DIR/drafts"
mkdir -p "$ARCHIVE_DIR/dashboard"
mkdir -p "$ARCHIVE_DIR/scripts"
mkdir -p "$ARCHIVE_DIR/.github/workflows"
mkdir -p "$ARCHIVE_DIR/archive"

echo "=== 1. 核心文档 ==="
cp "$LOCAL_DIR/PROJECT.md" "$ARCHIVE_DIR/"
cp "$LOCAL_DIR/README.md" "$ARCHIVE_DIR/"
cp "$LOCAL_DIR/ARCHITECTURE_FOUR_LAYER.md" "$ARCHIVE_DIR/"
cp "$LOCAL_DIR/DOMAIN_INDEX.md" "$ARCHIVE_DIR/"
cp "$LOCAL_DIR/FOUR_TIER_SYSTEM_DESIGN.md" "$ARCHIVE_DIR/"
cp "$LOCAL_DIR/KANBAN_SOFTWARE_ENGINEERING.md" "$ARCHIVE_DIR/"
cp "$LOCAL_DIR/requirements-analysis.md" "$ARCHIVE_DIR/docs/"
echo "  ✓ 核心文档"

echo "=== 2. 领域规范（8 领域 × 120 学科）==="
cp "$LOCAL_DIR/domain-specs/"*.md "$ARCHIVE_DIR/domain-specs/"
echo "  ✓ $(ls "$LOCAL_DIR/domain-specs/"*.md 2>/dev/null | wc -l) 个规范文件"

echo "=== 3. 看板网页 ==="
cp "$LOCAL_DIR/dashboard/index.html" "$ARCHIVE_DIR/dashboard/"
echo "  ✓ dashboard/index.html"

echo "=== 4. CI/CD 工作流 ==="
cp "$LOCAL_DIR/.github/workflows/"*.yml "$ARCHIVE_DIR/.github/workflows/" 2>/dev/null || echo "  ⚠ 无 workflow 文件"
echo "  ✓ CI/CD 配置"

echo "=== 5. 草稿与章节 ==="
cp -r "$LOCAL_DIR/drafts/"* "$ARCHIVE_DIR/drafts/" 2>/dev/null || echo "  ⚠ 无草稿文件"
echo "  ✓ 草稿文件"

echo "=== 6. 部署脚本 ==="
cp "$LOCAL_DIR/scripts/"*.sh "$ARCHIVE_DIR/scripts/"
echo "  ✓ 部署脚本"

echo "=== 7. 创建版本索引 ==="
cat > "$ARCHIVE_DIR/INDEX.md" << 'INDEX'
# 中医教材编写平台的文档归档

## 归档信息
- **归档时间**: $(date '+%Y-%m-%d %H:%M')
- **归档位置**: F:/hermes/
- **项目名称**: 中医教材编写平台的文档
- **版本**: v1.0

## 目录结构
| 目录 | 说明 | 文件数 |
|:----|------|:-----:|
| `/` | 项目核心文档 | 7 |
| `docs/` | 需求分析等 | 1 |
| `domain-specs/` | 8 领域 × 120 学科规范 | 8+ |
| `drafts/` | 编写草稿 | 按需 |
| `dashboard/` | 统筹看板网页 | 1 |
| `scripts/` | 部署与运维脚本 | 4 |
| `.github/workflows/` | CI/CD 工作流 | 2 |
| `archive/` | 历史归档 | — |

## 相关系统
- GitHub: https://github.com/beijingcdy/tcm-textbook-series
- 云服务器: http://114.115.211.254 (华为云)
- 后端服务器: 192.168.1.12 (华为硬服务器)
- Hermes API: http://localhost:8642
- 看板前端: http://localhost:8000
INDEX

echo ""
echo "=== ✅ 归档完成 ==="
echo "目标: $ARCHIVE_DIR"
echo "文件数: $(find "$ARCHIVE_DIR" -type f | wc -l)"
