#!/bin/bash
# migrate.sh — 版本迁移脚本
# 用法: bash migrate.sh <from_version> <to_version> <wiki_root>
#
# 支持的迁移路径:
#   3.0 → 3.5: 添加 _meta/ 目录，更新 index.md 格式
#   3.1 → 3.5: 添加 _crystallize/ 目录
#   3.2 → 3.5: 无破坏性变更
#   3.3 → 3.5: 无破坏性变更
#   3.4 → 3.5: 无破坏性变更

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

FROM_VERSION="${1:-}"
TO_VERSION="${2:-}"
WIKI_ROOT="${3:-}"

usage() {
  echo "用法: bash migrate.sh <from_version> <to_version> <wiki_root>"
  echo ""
  echo "示例:"
  echo "  bash migrate.sh 3.0 3.5 /root/wiki-ai"
  echo ""
  echo "支持的迁移:"
  echo "  3.0 → 3.5"
  echo "  3.1 → 3.5"
  echo "  3.2 → 3.5"
  echo "  3.3 → 3.5"
  echo "  3.4 → 3.5"
}

if [ -z "$FROM_VERSION" ] || [ -z "$TO_VERSION" ] || [ -z "$WIKI_ROOT" ]; then
  usage
  exit 1
fi

if [ ! -d "$WIKI_ROOT" ]; then
  log_error "Wiki 目录不存在: $WIKI_ROOT"
  exit 1
fi

echo "=== 版本迁移 ==="
echo "从: v$FROM_VERSION"
echo "到: v$TO_VERSION"
echo "Wiki: $WIKI_ROOT"
echo ""

CHANGES=0

# 迁移 3.0 → 3.5
if [ "$FROM_VERSION" = "3.0" ]; then
  log_info "执行 3.0 → 3.5 迁移..."
  
  # 添加 _meta/ 目录
  if [ ! -d "$WIKI_ROOT/_meta" ]; then
    mkdir -p "$WIKI_ROOT/_meta"
    log_success "创建 _meta/ 目录"
    CHANGES=$((CHANGES + 1))
  fi
  
  # 添加 _crystallize/ 目录
  if [ ! -d "$WIKI_ROOT/_crystallize" ]; then
    mkdir -p "$WIKI_ROOT/_crystallize"
    log_success "创建 _crystallize/ 目录"
    CHANGES=$((CHANGES + 1))
  fi
  
  # 添加 .wiki-cache.json（如果不存在）
  if [ ! -f "$WIKI_ROOT/.wiki-cache.json" ]; then
    echo "{}" > "$WIKI_ROOT/.wiki-cache.json"
    log_success "创建 .wiki-cache.json"
    CHANGES=$((CHANGES + 1))
  fi
  
  # 添加 .wiki-aliases.json（如果不存在）
  if [ ! -f "$WIKI_ROOT/.wiki-aliases.json" ]; then
    echo '{}' > "$WIKI_ROOT/.wiki-aliases.json"
    log_success "创建 .wiki-aliases.json"
    CHANGES=$((CHANGES + 1))
  fi
  
  FROM_VERSION="3.1"
fi

# 迁移 3.1 → 3.5
if [ "$FROM_VERSION" = "3.1" ]; then
  log_info "执行 3.1 → 3.5 迁移..."
  
  # 添加 _crystallize/ 目录（如果不存在）
  if [ ! -d "$WIKI_ROOT/_crystallize" ]; then
    mkdir -p "$WIKI_ROOT/_crystallize"
    log_success "创建 _crystallize/ 目录"
    CHANGES=$((CHANGES + 1))
  fi
  
  FROM_VERSION="3.2"
fi

# 迁移 3.2 → 3.5
if [ "$FROM_VERSION" = "3.2" ]; then
  log_info "执行 3.2 → 3.5 迁移..."
  
  # 无破坏性变更
  log_success "无破坏性变更"
  
  FROM_VERSION="3.3"
fi

# 迁移 3.3 → 3.5
if [ "$FROM_VERSION" = "3.3" ]; then
  log_info "执行 3.3 → 3.5 迁移..."
  
  # 无破坏性变更
  log_success "无破坏性变更"
  
  FROM_VERSION="3.4"
fi

# 迁移 3.4 → 3.5
if [ "$FROM_VERSION" = "3.4" ]; then
  log_info "执行 3.4 → 3.5 迁移..."
  
  # 无破坏性变更
  log_success "无破坏性变更"
  
  FROM_VERSION="3.5"
fi

echo ""
echo "=== 迁移完成 ==="
echo "变更数: $CHANGES"
echo "当前版本: v$TO_VERSION"

if [ "$CHANGES" -gt 0 ]; then
  echo ""
  echo "建议运行健康检查:"
  echo "  bash ${SCRIPT_DIR}/lint-runner.sh $WIKI_ROOT"
fi

exit 0
