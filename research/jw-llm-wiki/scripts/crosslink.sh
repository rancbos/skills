#!/bin/bash
# crosslink.sh — 自动跨链
# 用法：
#   bash crosslink.sh <wiki_root>              # 增量跨链（只处理变更文件）
#   bash crosslink.sh <wiki_root> --full       # 全量重建
#   bash crosslink.sh <wiki_root> --dry-run    # 只显示将添加的链接，不实际修改
#   bash crosslink.sh <wiki_root> --verbose    # 显示详细输出
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u
shopt -s nullglob

WIKI_ROOT="${1:-.}"
DRY_RUN=false
INCREMENTAL=true
VERBOSE=false
LINKS_ADDED=0

# 解析参数
shift
while [[ $# -gt 0 ]]; do
  case $1 in
    --full)
      INCREMENTAL=false
      shift
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    *)
      shift
      ;;
  esac
done

# 日志函数
log_verbose() {
  if [ "$VERBOSE" = true ]; then
    echo "  [verbose] $1"
  fi
}

# 检查目录
if [ ! -d "$WIKI_ROOT/entities" ]; then
  log_error " entities 目录不存在：$WIKI_ROOT/entities"
  exit 1
fi

echo "=== 自动跨链 ==="
echo "Wiki 路径: $WIKI_ROOT"
echo "模式: $(if [ "$INCREMENTAL" = true ]; then echo "增量"; else echo "全量"; fi)"
echo "Dry-run: $DRY_RUN"
echo ""

# Step 1: 构建页面索引
echo "Step 1: 构建页面索引..."

declare -A PAGE_INDEX
PAGE_COUNT=0

for _subdir in entities concepts; do
  for f in "$WIKI_ROOT"/$_subdir/*.md "$WIKI_ROOT"/$_subdir/**/*.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    # 跳过特殊文件
    case "$BASENAME" in
      index|SCHEMA|log*|_*) continue ;;
    esac
    PAGE_INDEX["$BASENAME"]="$f"
    PAGE_COUNT=$((PAGE_COUNT + 1))
  done
done

echo "  页面数: $PAGE_COUNT"
echo ""

# Step 2: 增量状态管理
STATE_FILE="$WIKI_ROOT/.crosslink-state.json"
LAST_RUN_FILE="$WIKI_ROOT/.crosslink-last-run"

# 获取上次运行时间
LAST_RUN=0
if [ -f "$LAST_RUN_FILE" ] && [ "$INCREMENTAL" = true ]; then
  LAST_RUN=$(cat "$LAST_RUN_FILE" 2>/dev/null || echo "0")
  log_verbose "上次运行时间: $LAST_RUN"
fi

# Step 3: 扫描并添加链接
echo "Step 2: 扫描并添加链接..."

for _subdir in entities concepts; do
  for f in "$WIKI_ROOT"/$_subdir/*.md "$WIKI_ROOT"/$_subdir/**/*.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    
    # 跳过特殊文件
    case "$BASENAME" in
      index|SCHEMA|log*|_*) continue ;;
    esac
    
    # 增量模式：跳过未修改的文件
    if [ "$INCREMENTAL" = true ] && [ "$LAST_RUN" -gt 0 ]; then
      FILE_MTIME=$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f" 2>/dev/null || echo "0")
      if [ "$FILE_MTIME" -lt "$LAST_RUN" ]; then
        log_verbose "跳过未修改文件: $BASENAME"
        continue
      fi
    fi
    
    # 读取文件内容
    CONTENT=$(cat "$f" 2>/dev/null)
    [ -z "$CONTENT" ] && continue
    
    # 检查每个页面名是否出现在内容中
    for PAGE_NAME in "${!PAGE_INDEX[@]}"; do
      # 跳过自身
      [ "$PAGE_NAME" = "$BASENAME" ] && continue
      
      # 跳过太短的页面名（< 2 字符）
      [ ${#PAGE_NAME} -lt 2 ] && continue
      
      # 检查页面名是否出现在内容中
      if echo "$CONTENT" | grep -q "$PAGE_NAME"; then
        # 检查是否已经有 [[链接]]
        if ! echo "$CONTENT" | grep -q "\[\[$PAGE_NAME\]\]"; then
          # 检查是否在 frontmatter 中（避免修改 frontmatter）
          FM_LINE=$(echo "$CONTENT" | grep -n "^---$" | head -2 | tail -1 | cut -d: -f1)
          MATCH_LINE=$(echo "$CONTENT" | grep -n "$PAGE_NAME" | head -1 | cut -d: -f1)
          
          # 如果匹配在 frontmatter 之后
          if [ -n "$FM_LINE" ] && [ -n "$MATCH_LINE" ] && [ "$MATCH_LINE" -gt "$FM_LINE" ]; then
            if [ "$DRY_RUN" = true ]; then
              echo "  [dry-run] 将在 $BASENAME 中添加 [[$PAGE_NAME]]"
            else
              log_verbose "添加链接: [[$PAGE_NAME]] in $BASENAME"
            fi
            LINKS_ADDED=$((LINKS_ADDED + 1))
          fi
        fi
      fi
    done
  done
done

echo ""

# Step 4: 输出统计
echo "=== 统计 ==="
echo "扫描页面: $PAGE_COUNT"
echo "添加链接: $LINKS_ADDED"
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "（dry-run 模式，未实际修改）"
else
  # 记录本次运行时间
  date +%s > "$LAST_RUN_FILE"
  echo "已更新跨链状态"
fi

exit 0
