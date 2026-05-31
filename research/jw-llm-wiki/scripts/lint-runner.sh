#!/bin/bash
# lint-runner.sh — Wiki 机械健康检查
# 用法：bash lint-runner.sh <wiki_root>
# 输出：结构化文本报告（供 AI 后续分析使用）
# 退出码：0 = 运行完成，1 = 脚本错误（路径不存在、wiki 结构不完整）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u
shopt -s nullglob

WIKI_ROOT="${1:-.}"
INDEX_FILE="$WIKI_ROOT/index.md"

if [ ! -d "$WIKI_ROOT/entities" ]; then
  log_error "entities 目录不存在：$WIKI_ROOT/entities"
  echo "       请确认路径正确，或先运行 init 工作流初始化知识库。"
  exit 1
fi
if [ ! -f "$INDEX_FILE" ]; then
  log_error "index.md 不存在：$INDEX_FILE"
  exit 1
fi

# 辅助函数：检查 index.md 中是否有某个条目
index_has_entry() {
  local entry="$1"
  grep -ohE "\[\[[^]]+\]\]" "$INDEX_FILE" 2>/dev/null | \
    sed -e 's/\[\[//g' -e 's/\]\]//g' -e 's/|.*//' | \
    grep -Fxq "$entry"
}

# 辅助函数：检查页面是否存在
page_exists() {
  local page="$1"
  for subdir in entities concepts comparisons queries; do
    if [ -f "$WIKI_ROOT/$subdir/$page.md" ]; then
      return 0
    fi
    # 检查子目录
    if find "$WIKI_ROOT/$subdir" -name "$page.md" 2>/dev/null | grep -q .; then
      return 0
    fi
  done
  return 1
}

echo "=== jw-llm-wiki lint 报告 ==="
echo "时间：$(date '+%Y-%m-%d %H:%M')"
echo "检查路径：$WIKI_ROOT"
echo ""

# 检查 1：孤立页面
# 定义：entities/、concepts/ 下的页面，除了自己之外没有任何其他 wiki 页面用 [[名称]] 引用它
echo "--- 孤立页面（没有被其他页面引用） ---"
_ORPHANS=0
for _subdir in entities concepts; do
  for f in "$WIKI_ROOT"/$_subdir/*.md "$WIKI_ROOT"/$_subdir/**/*.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    # 跳过 index.md
    [ "$BASENAME" = "index" ] && continue
    if ! grep -rlF "[[$BASENAME]]" "$WIKI_ROOT" 2>/dev/null | grep -vxF "$f" | grep -q .; then
      echo "  孤立: $_subdir/$BASENAME"
      _ORPHANS=$((_ORPHANS + 1))
    fi
  done
done
[ "$_ORPHANS" -eq 0 ] && echo "  （无孤立页面）"
echo "  总计: $_ORPHANS 个孤立页面"
echo ""

# 检查 2：断链
# 定义：wiki 下的页面里有 [[X]] 链接（支持 [[X|别名]] 语法），但 wiki 任意子目录找不到 X.md
echo "--- 断链（被链接但不存在的页面） ---"
_BROKEN=0
_TMP_BROKEN=$(mktemp)
grep -rohE "\[\[[^]]+\]\]" "$WIKI_ROOT" 2>/dev/null | \
  sed -e 's/\[\[//g' -e 's/\]\]//g' -e 's/|.*//' | \
  sort -u | \
  while read -r LINK; do
    [ -z "$LINK" ] && continue
    # 跳过特殊链接
    case "$LINK" in
      wikilinks*|SCHEMA*|index*|http*|mailto*) continue ;;
      index*|http*|mailto*) continue ;;
    esac
    if ! page_exists "$LINK"; then
      echo "  断链: [[$LINK]]"
      echo "$LINK" >> "$_TMP_BROKEN"
    fi
  done
if [ -s "$_TMP_BROKEN" ]; then
  _BROKEN=$(wc -l < "$_TMP_BROKEN")
else
  echo "  （无断链）"
fi
rm -f "$_TMP_BROKEN"
echo ""

# 检查 3：index 一致性
# 定义：index.md 里有 [[X]] 记录（去掉别名），但 wiki 任意子目录都找不到 X.md
echo "--- index 一致性（index.md 有记录但文件缺失） ---"
_TMP_MISSING=$(mktemp)
grep -ohE "\[\[[^]]+\]\]" "$INDEX_FILE" 2>/dev/null | \
  sed -e 's/\[\[//g' -e 's/\]\]//g' -e 's/|.*//' | \
  sort -u | \
  while read -r ENTRY; do
    [ -z "$ENTRY" ] && continue
    if ! page_exists "$ENTRY"; then
      echo "  index 有但文件缺失: $ENTRY"
      echo "$ENTRY" >> "$_TMP_MISSING"
    fi
  done
if [ ! -s "$_TMP_MISSING" ]; then
  echo "  （index 与文件一致）"
fi
rm -f "$_TMP_MISSING"
echo ""

# 检查 4：反向 index 一致性
# 定义：wiki 下实际存在的页面，但 index.md 里没有 [[页面名]] 记录
echo "--- 反向 index 一致性（文件存在但 index.md 未收录） ---"
_TMP_UNLISTED=$(mktemp)
for _subdir in entities concepts comparisons queries; do
  for f in "$WIKI_ROOT"/$_subdir/*.md "$WIKI_ROOT"/$_subdir/**/*.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    # 跳过特殊文件
    case "$BASENAME" in
      index|SCHEMA|log*) continue ;;
    esac
    if ! index_has_entry "$BASENAME"; then
      echo "  未收录: $_subdir/$BASENAME"
      echo "$BASENAME" >> "$_TMP_UNLISTED"
    fi
  done
done
if [ ! -s "$_TMP_UNLISTED" ]; then
  echo "  （所有页面均已收录）"
fi
rm -f "$_TMP_UNLISTED"
echo ""

# 检查 5：frontmatter 验证
# 定义：检查必需的 frontmatter 字段是否存在
echo "--- frontmatter 验证 ---"
_FM_ISSUES=0
for _subdir in entities concepts; do
  for f in "$WIKI_ROOT"/$_subdir/*.md "$WIKI_ROOT"/$_subdir/**/*.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    
    # 读取 frontmatter
    _FM=$(sed -n '/^---$/,/^---$/p' "$f" 2>/dev/null)
    [ -z "$_FM" ] && continue
    
    # 检查必需字段
    _MISSING=""
    for _field in title created updated type tags; do
      if ! echo "$_FM" | grep -q "^$_field:"; then
        _MISSING="$_MISSING $_field"
      fi
    done
    
    if [ -n "$_MISSING" ]; then
      echo "  $_subdir/$BASENAME: 缺少字段$_MISSING"
      _FM_ISSUES=$((_FM_ISSUES + 1))
    fi
  done
done
[ "$_FM_ISSUES" -eq 0 ] && echo "  （所有 frontmatter 完整）"
echo "  总计: $_FM_ISSUES 个页面有问题"
echo ""

# 检查 6：大页面检查
# 定义：超过 200 行的页面
echo "--- 大页面检查（超过 200 行） ---"
_LARGE=0
for _subdir in entities concepts comparisons queries; do
  for f in "$WIKI_ROOT"/$_subdir/*.md "$WIKI_ROOT"/$_subdir/**/*.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    LINES=$(wc -l < "$f" 2>/dev/null || echo "0")
    if [ "$LINES" -gt 200 ]; then
      echo "  $_subdir/$BASENAME: $LINES 行"
      _LARGE=$((_LARGE + 1))
    fi
  done
done
[ "$_LARGE" -eq 0 ] && echo "  （无大页面）"
echo "  总计: $_LARGE 个大页面"
echo ""

# 检查 7：标签审计
# 定义：检查页面上使用的标签是否在 SCHEMA.md 中登记
echo "--- 标签审计 ---"
_SCHEMA_FILE="$WIKI_ROOT/SCHEMA.md"
if [ -f "$_SCHEMA_FILE" ]; then
  # 提取 SCHEMA 中的标签
  _SCHEMA_TAGS=$(grep -oE '[\u4e00-\u9fa5a-zA-Z]+' "$_SCHEMA_FILE" 2>/dev/null | sort -u)
  
  # 提取页面中的标签
  _PAGE_TAGS=$(grep -rh "^tags:" "$WIKI_ROOT"/entities/ "$WIKI_ROOT"/concepts/ 2>/dev/null | \
    sed 's/tags: \[//;s/\]//;s/,/\n/g' | \
    sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | \
    sed 's/"//g' | \
    sort -u)
  
  # 找出未登记的标签
  _UNREGISTERED=0
  while read -r tag; do
    [ -z "$tag" ] && continue
    if ! echo "$_SCHEMA_TAGS" | grep -qF "$tag"; then
      echo "  未登记标签: $tag"
      _UNREGISTERED=$((_UNREGISTERED + 1))
    fi
  done <<< "$_PAGE_TAGS"
  
  [ "$_UNREGISTERED" -eq 0 ] && echo "  （所有标签已登记）"
  echo "  总计: $_UNREGISTERED 个未登记标签"
else
  echo "  （SCHEMA.md 不存在，跳过标签审计）"
fi
echo ""

# 检查 8：置信度统计
echo "--- 置信度统计 ---"
_CONFIDENCE_COUNTS=""
for _level in EXTRACTED INFERRED AMBIGUOUS UNVERIFIED; do
  _COUNT=$(grep -rh "confidence: $_level" "$WIKI_ROOT"/entities/ "$WIKI_ROOT"/concepts/ 2>/dev/null | wc -l)
  echo "  $_level: $_COUNT"
done
echo ""

# 检查 9：来源完整性
echo "--- 来源完整性 ---"
_NO_SOURCES=0
for _subdir in entities concepts; do
  for f in "$WIKI_ROOT"/$_subdir/*.md "$WIKI_ROOT"/$_subdir/**/*.md; do
    [ -f "$f" ] || continue
    BASENAME=$(basename "$f" .md)
    
    # 检查是否有 sources 字段
    if ! grep -q "^sources:" "$f" 2>/dev/null; then
      echo "  $_subdir/$BASENAME: 缺少 sources 字段"
      _NO_SOURCES=$((_NO_SOURCES + 1))
    fi
  done
done
[ "$_NO_SOURCES" -eq 0 ] && echo "  （所有页面有 sources 字段）"
echo "  总计: $_NO_SOURCES 个页面缺少 sources"
echo ""

# 总结
echo "=== 总结 ==="
echo "孤立页面: $_ORPHANS"
echo "frontmatter 问题: $_FM_ISSUES"
echo "大页面: $_LARGE"
echo "缺少 sources: $_NO_SOURCES"
echo ""

# 判断是否需要 AI 介入
_NEEDS_AI=false
if [ "$_ORPHANS" -gt 0 ] || [ "$_FM_ISSUES" -gt 0 ]; then
  _NEEDS_AI=true
fi

if [ "$_NEEDS_AI" = true ]; then
  echo "需要 AI 介入的问题："
  [ "$_ORPHANS" -gt 0 ] && echo "  - 孤立页面需要添加交叉引用"
  [ "$_FM_ISSUES" -gt 0 ] && echo "  - frontmatter 需要补全"
  echo ""
  echo "请将此报告交给 AI，由 AI 判断如何修复。"
fi

exit 0
