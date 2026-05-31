#!/bin/bash
# lint-fix.sh — 自动修复 lint 发现的低风险问题
# 用法：bash lint-fix.sh <wiki_root> [--dry-run]
# 修复范围：仅处理确定性修复（补 index 条目），不做高风险操作（删页面、改内容）
# 退出码：0 = 完成，1 = 参数错误
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u
shopt -s nullglob

WIKI_ROOT="${1:-.}"
DRY_RUN=false
[ "${2:-}" = "--dry-run" ] && DRY_RUN=true

INDEX_FILE="$WIKI_ROOT/index.md"

if [ ! -d "$WIKI_ROOT/entities" ]; then
  log_error " entities 目录不存在：$WIKI_ROOT/entities"
  exit 1
fi
if [ ! -f "$INDEX_FILE" ]; then
  log_error " index.md 不存在：$INDEX_FILE"
  exit 1
fi

FIXED=0

index_has_entry() {
  local entry="$1"
  grep -ohE "\[\[[^]]+\]\]" "$INDEX_FILE" 2>/dev/null | \
    sed -e 's/\[\[//g' -e 's/\]\]//g' -e 's/|.*//' | \
    grep -Fxq "$entry"
}

# 在 index.md 的对应分节下插入条目
insert_under_section() {
  local index_file="$1"
  local section_pattern="$2"
  local entry="$3"

  # 找到分节标题的行号
  local line_num
  line_num=$(grep -n -i -E "^#.*($section_pattern)" "$index_file" 2>/dev/null | head -1 | cut -d: -f1)

  if [ -n "$line_num" ]; then
    # 从分节标题开始扫描，找到插入点：
    # 最后一个 "- [[" 行，直到下一个 "##" 标题或 EOF
    local total_lines last_list_line offset
    total_lines=$(wc -l < "$index_file" | tr -d ' ')
    last_list_line="$line_num"
    offset=$((line_num + 1))
    while [ "$offset" -le "$total_lines" ]; do
      local cur_line
      cur_line=$(sed -n "${offset}p" "$index_file")
      case "$cur_line" in
        "##"*) break ;;
        "- [["*) last_list_line="$offset" ;;
      esac
      offset=$((offset + 1))
    done
    # 在最后一个列表项后插入
    local tmp_file
    tmp_file=$(mktemp "${index_file}.tmp.XXXXXX") || return 1
    awk -v insert_after="$last_list_line" -v entry="$entry" '
      { print }
      NR == insert_after { print "- [[" entry "]]" }
    ' "$index_file" > "$tmp_file" && mv "$tmp_file" "$index_file"
  else
    # 回退：追加到文件末尾
    printf '\n- [[%s]]\n' "$entry" >> "$index_file"
  fi
}

echo "=== lint-fix: 低风险自动修复 ==="
echo ""

# 修复 1：将未收录的页面添加到 index.md
echo "--- 检查未收录页面 ---"
for _subdir in entities concepts comparisons queries; do
  for f in "$WIKI_ROOT"/$_subdir/*.md "$WIKI_ROOT"/$_subdir/**/*.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    # 跳过特殊文件
    case "$BASENAME" in
      index|SCHEMA|log*|_*) continue ;;
    esac
    if ! index_has_entry "$BASENAME"; then
      # 确定分节
      SECTION_PATTERN=""
      case "$_subdir" in
        entities) SECTION_PATTERN="实体|Entities" ;;
        concepts) SECTION_PATTERN="概念|Concepts" ;;
        comparisons) SECTION_PATTERN="对比|Comparisons" ;;
        queries) SECTION_PATTERN="查询|Queries" ;;
      esac
      if [ "$DRY_RUN" = true ]; then
        echo "  [dry-run] 将添加 [[$BASENAME]] 到 $_subdir 分节"
      else
        insert_under_section "$INDEX_FILE" "$SECTION_PATTERN" "$BASENAME"
        echo "  已添加 [[$BASENAME]] 到 $_subdir 分节"
        FIXED=$((FIXED + 1))
      fi
    fi
  done
done
echo ""

# 修复 2：更新 index.md 头部的统计数字
echo "--- 更新 index.md 统计数字 ---"
if [ "$DRY_RUN" = true ]; then
  echo "  [dry-run] 将更新统计数字"
else
  # 统计各分类页面数
  ENTITY_COUNT=$(find "$WIKI_ROOT/entities" -name "*.md" -type f 2>/dev/null | wc -l)
  CONCEPT_COUNT=$(find "$WIKI_ROOT/concepts" -name "*.md" -type f 2>/dev/null | wc -l)
  COMPARISON_COUNT=$(find "$WIKI_ROOT/comparisons" -name "*.md" -type f 2>/dev/null | wc -l)
  QUERY_COUNT=$(find "$WIKI_ROOT/queries" -name "*.md" -type f 2>/dev/null | wc -l)
  TOTAL=$((ENTITY_COUNT + CONCEPT_COUNT + COMPARISON_COUNT + QUERY_COUNT))
  
  # 统计传统文化和投资
  TRAD_COUNT=$(find "$WIKI_ROOT/entities" -name "*.md" -type f 2>/dev/null | xargs grep -l "category: rujia\|category: dao\|category: fo\|category: fajia\|category: baojia\|category: bingjia\|category: lishi\|category: zhongyi\|category: mengxue\|category: nanhuaijin" 2>/dev/null | wc -l)
  INVEST_COUNT=$(find "$WIKI_ROOT/entities" -name "*.md" -type f 2>/dev/null | xargs grep -l "category: invest" 2>/dev/null | wc -l)
  MALIE_COUNT=$(find "$WIKI_ROOT/entities" -name "*.md" -type f 2>/dev/null | xargs grep -l "category: malie" 2>/dev/null | wc -l)
  
  # 更新头部
  sed -i "s/最后更新：.*| 总计：.*/最后更新：$(date +%Y-%m-%d) | 总计：${TOTAL}页 (entity ${ENTITY_COUNT} + concept ${CONCEPT_COUNT})/" "$INDEX_FILE"
  
  echo "  已更新统计数字：总计 $TOTAL 页"
  FIXED=$((FIXED + 1))
fi
echo ""

# 修复 3：补全 concept 页面的 category 字段
echo "--- 检查 concept 页面 category ---"
for f in "$WIKI_ROOT/concepts"/*.md; do
  [ -f "$f" ] || continue
  BASENAME=$(basename "$f" .md)
  
  # 检查是否有 category 字段
  if ! grep -q "^category:" "$f" 2>/dev/null; then
    if [ "$DRY_RUN" = true ]; then
      echo "  [dry-run] 将为 $BASENAME 添加 category: concepts"
    else
      # 在 type: concept 后面添加 category: concepts
      sed -i '/^type: concept$/a category: concepts' "$f"
      echo "  已为 $BASENAME 添加 category: concepts"
      FIXED=$((FIXED + 1))
    fi
  fi
done
echo ""

# 总结
echo "=== 总结 ==="
if [ "$DRY_RUN" = true ]; then
  echo "（dry-run 模式，未实际修改）"
else
  echo "已修复: $FIXED 个问题"
fi

exit 0
