#!/bin/bash
# confidence-stats.sh — 置信度统计脚本
# 用法：bash confidence-stats.sh <wiki_root>
# 输出：各置信度级别的数量和百分比
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u

WIKI_ROOT="${1:-.}"

# 检测 wiki 目录结构
if [ -d "$WIKI_ROOT/wiki" ]; then
  WIKI_DIR="$WIKI_ROOT/wiki"
elif [ -d "$WIKI_ROOT/entities" ]; then
  WIKI_DIR="$WIKI_ROOT"
else
  log_error " 无法找到 wiki 目录"
  exit 1
fi

echo "=== 置信度统计报告 ==="
echo "检查路径：$WIKI_DIR"
echo ""

# 统计各置信度数量
EXTRACTED=0
INFERRED=0
AMBIGUOUS=0
UNVERIFIED=0
NO_CONFIDENCE=0
TOTAL=0

for subdir in entities concepts comparisons queries; do
  for f in "$WIKI_DIR/$subdir"/*.md; do
    [ -f "$f" ] || continue
    ((TOTAL++))
    
    # 从 frontmatter 提取 confidence
    confidence=$(grep -m1 "^confidence:" "$f" 2>/dev/null | sed 's/confidence: *//' | tr -d ' ')
    
    case "$confidence" in
      EXTRACTED) ((EXTRACTED++)) ;;
      INFERRED) ((INFERRED++)) ;;
      AMBIGUOUS) ((AMBIGUOUS++)) ;;
      UNVERIFIED) ((UNVERIFIED++)) ;;
      *) ((NO_CONFIDENCE++)) ;;
    esac
  done
done

# 计算百分比
if [ $TOTAL -gt 0 ]; then
  EXTRACTED_PCT=$((EXTRACTED * 100 / TOTAL))
  INFERRED_PCT=$((INFERRED * 100 / TOTAL))
  AMBIGUOUS_PCT=$((AMBIGUOUS * 100 / TOTAL))
  UNVERIFIED_PCT=$((UNVERIFIED * 100 / TOTAL))
  NO_CONFIDENCE_PCT=$((NO_CONFIDENCE * 100 / TOTAL))
else
  EXTRACTED_PCT=0
  INFERRED_PCT=0
  AMBIGUOUS_PCT=0
  UNVERIFIED_PCT=0
  NO_CONFIDENCE_PCT=0
fi

echo "总页面数：$TOTAL"
echo ""
echo "置信度分布："
echo "  EXTRACTED（原文摘录）：$EXTRACTED ($EXTRACTED_PCT%)"
echo "  INFERRED（推断）：$INFERRED ($INFERRED_PCT%)"
echo "  AMBIGUOUS（有歧义）：$AMBIGUOUS ($AMBIGUOUS_PCT%)"
echo "  UNVERIFIED（未验证）：$UNVERIFIED ($UNVERIFIED_PCT%)"
echo "  未设置：$NO_CONFIDENCE ($NO_CONFIDENCE_PCT%)"
echo ""

# 列出需要验证的页面（AMBIGUOUS 和 UNVERIFIED）
if [ $AMBIGUOUS -gt 0 ] || [ $UNVERIFIED -gt 0 ]; then
  echo "需要验证的页面："
  for subdir in entities concepts comparisons queries; do
    for f in "$WIKI_DIR/$subdir"/*.md; do
      [ -f "$f" ] || continue
      confidence=$(grep -m1 "^confidence:" "$f" 2>/dev/null | sed 's/confidence: *//' | tr -d ' ')
      
      if [ "$confidence" = "AMBIGUOUS" ] || [ "$confidence" = "UNVERIFIED" ]; then
        basename_f=$(basename "$f" .md)
        echo "  - [[$basename_f]] ($confidence)"
      fi
    done
  done
fi
