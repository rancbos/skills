#!/bin/bash
# source-signal-coverage.sh — 来源信号覆盖检查
# 用法：
#   bash source-signal-coverage.sh <wiki_root>   # 检查来源完整性
#   bash source-signal-coverage.sh <wiki_root> --fix  # 自动修复（为空 sources 添加占位符）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u
shopt -s nullglob

WIKI_ROOT="${1:-.}"
FIX_MODE=false
[ "${2:-}" = "--fix" ] && FIX_MODE=true

INDEX_FILE="$WIKI_ROOT/index.md"

if [ ! -d "$WIKI_ROOT/entities" ]; then
  log_error " entities 目录不存在：$WIKI_ROOT/entities"
  exit 1
fi

echo "=== 来源信号覆盖检查 ==="
echo "Wiki 路径: $WIKI_ROOT"
echo ""

# 统计
OK=0
MISSING_SOURCES=0
EMPTY_SOURCES=0
INVALID_SOURCES=0
NOT_APPLICABLE=0

# 临时文件
ISSUES_FILE=$(mktemp)

# 检查所有实体和概念页面
for _subdir in entities concepts; do
  for f in "$WIKI_ROOT"/$_subdir/*.md "$WIKI_ROOT"/$_subdir/**/*.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    
    # 跳过特殊文件
    case "$BASENAME" in
      index|SCHEMA|log*|_*) 
        NOT_APPLICABLE=$((NOT_APPLICABLE + 1))
        continue 
        ;;
    esac
    
    # 读取 frontmatter
    _FM=$(sed -n '/^---$/,/^---$/p' "$f" 2>/dev/null)
    [ -z "$_FM" ] && continue
    
    # 检查 sources 字段
    _SOURCES_LINE=$(echo "$_FM" | grep "^sources:")
    
    if [ -z "$_SOURCES_LINE" ]; then
      # 缺少 sources 字段
      MISSING_SOURCES=$((MISSING_SOURCES + 1))
      echo "$_subdir/$BASENAME: 缺少 sources 字段" >> "$ISSUES_FILE"
      
      if [ "$FIX_MODE" = true ]; then
        # 在 frontmatter 末尾添加 sources: []
        sed -i '/^---$/i sources: []' "$f"
        echo "  已修复: 添加 sources: []"
      fi
    else
      # 检查 sources 是否为空
      _SOURCES_VALUE=$(echo "$_SOURCES_LINE" | sed 's/sources: *//')
      
      if [ "$_SOURCES_VALUE" = "[]" ] || [ -z "$_SOURCES_VALUE" ]; then
        # sources 为空
        EMPTY_SOURCES=$((EMPTY_SOURCES + 1))
        echo "$_subdir/$BASENAME: sources 为空" >> "$ISSUES_FILE"
      else
        # 检查 sources 格式是否有效
        if echo "$_SOURCES_VALUE" | grep -qE '^\[.*\]$'; then
          OK=$((OK + 1))
        else
          INVALID_SOURCES=$((INVALID_SOURCES + 1))
          echo "$_subdir/$BASENAME: sources 格式无效: $_SOURCES_VALUE" >> "$ISSUES_FILE"
        fi
      fi
    fi
  done
done

# 输出统计
echo "=== 统计 ==="
echo "已参与 (ok): $OK"
echo "缺少 sources: $MISSING_SOURCES"
echo "sources 为空: $EMPTY_SOURCES"
echo "格式无效: $INVALID_SOURCES"
echo "不适用: $NOT_APPLICABLE"
echo ""

# 输出问题列表
if [ -s "$ISSUES_FILE" ]; then
  echo "=== 问题列表 ==="
  cat "$ISSUES_FILE"
  echo ""
fi

# 总结
TOTAL=$((OK + MISSING_SOURCES + EMPTY_SOURCES + INVALID_SOURCES))
if [ "$TOTAL" -gt 0 ]; then
  COVERAGE=$((OK * 100 / TOTAL))
  echo "=== 总结 ==="
  echo "来源覆盖率: $COVERAGE% ($OK/$TOTAL)"
  
  if [ "$COVERAGE" -lt 80 ]; then
    echo ""
    echo "⚠️  来源覆盖率低于 80%，建议："
    echo "1. 为缺少 sources 的页面添加来源信息"
    echo "2. 运行 bash source-signal-coverage.sh $WIKI_ROOT --fix 自动添加占位符"
  fi
fi

# 清理
rm -f "$ISSUES_FILE"

exit 0
