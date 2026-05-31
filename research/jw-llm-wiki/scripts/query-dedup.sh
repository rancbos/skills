#!/bin/bash
# query-dedup.sh — 查询去重 + 自引用防护
# 用法：
#   bash query-dedup.sh check "<主题>" <wiki_root>   # 检查是否已有同主题 query 页面
#   bash query-dedup.sh list <wiki_root>             # 列出所有 query 页面
#   bash query-dedup.sh stats <wiki_root>            # 统计 query 页面
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u

# 检查是否已有同主题 query 页面
check_duplicates() {
  local topic="$1"
  local wiki_root="$2"
  
  echo "=== 查询去重检查 ==="
  echo "主题: $topic"
  echo ""
  
  local query_dir="$wiki_root/queries"
  
  if [ ! -d "$query_dir" ]; then
    echo "queries/ 目录不存在，无重复"
    return 0
  fi
  
  # 搜索同主题的 query 页面
  local duplicates=""
  for f in "$query_dir"/*.md; do
    [ -f "$f" ] || continue
    local basename=$(basename "$f" .md)
    local title=$(grep "^title:" "$f" 2>/dev/null | head -1 | sed 's/title: *//')
    local tags=$(grep "^tags:" "$f" 2>/dev/null | head -1 | sed 's/tags: *//')
    
    # 检查标题或标签是否匹配
    if echo "$title" | grep -qi "$topic" || echo "$tags" | grep -qi "$topic"; then
      duplicates="$duplicates
$f"
    fi
  done
  
  duplicates=$(echo "$duplicates" | grep -v '^$')
  
  if [ -z "$duplicates" ]; then
    echo "✅ 未找到同主题的 query 页面"
    echo "可以安全创建新页面。"
    return 0
  fi
  
  echo "⚠️  找到同主题的 query 页面："
  while read -r page; do
    [ -z "$page" ] && continue
    local basename=$(basename "$page" .md)
    local title=$(grep "^title:" "$page" 2>/dev/null | head -1 | sed 's/title: *//')
    local created=$(grep "^created:" "$page" 2>/dev/null | head -1 | sed 's/created: *//')
    echo "  - $basename ($title, 创建于 $created)"
  done <<< "$duplicates"
  
  echo ""
  echo "建议："
  echo "  1. 更新现有页面（推荐）"
  echo "  2. 新建页面（需要用户确认）"
  
  return 1
}

# 列出所有 query 页面
list_queries() {
  local wiki_root="$1"
  
  echo "=== Query 页面列表 ==="
  echo ""
  
  local query_dir="$wiki_root/queries"
  
  if [ ! -d "$query_dir" ]; then
    echo "queries/ 目录不存在"
    return 0
  fi
  
  local count=0
  for f in "$query_dir"/*.md; do
    [ -f "$f" ] || continue
    local basename=$(basename "$f" .md)
    local title=$(grep "^title:" "$f" 2>/dev/null | head -1 | sed 's/title: *//')
    local created=$(grep "^created:" "$f" 2>/dev/null | head -1 | sed 's/created: *//')
    local derived=$(grep "^derived:" "$f" 2>/dev/null | head -1 | sed 's/derived: *//')
    
    echo "  - $basename"
    echo "    标题: $title"
    echo "    创建: $created"
    echo "    衍生: $derived"
    echo ""
    
    count=$((count + 1))
  done
  
  if [ "$count" -eq 0 ]; then
    echo "暂无 query 页面"
  else
    echo "总计: $count 个 query 页面"
  fi
}

# 统计 query 页面
stats_queries() {
  local wiki_root="$1"
  
  echo "=== Query 页面统计 ==="
  echo ""
  
  local query_dir="$wiki_root/queries"
  
  if [ ! -d "$query_dir" ]; then
    echo "queries/ 目录不存在"
    return 0
  fi
  
  local total=0
  local derived=0
  local non_derived=0
  
  for f in "$query_dir"/*.md; do
    [ -f "$f" ] || continue
    total=$((total + 1))
    
    local is_derived=$(grep "^derived:" "$f" 2>/dev/null | head -1 | sed 's/derived: *//')
    if [ "$is_derived" = "true" ]; then
      derived=$((derived + 1))
    else
      non_derived=$((non_derived + 1))
    fi
  done
  
  echo "总计: $total 个 query 页面"
  echo "  - 衍生内容: $derived"
  echo "  - 非衍生内容: $non_derived"
  echo ""
  
  if [ "$total" -gt 0 ]; then
    echo "自引用防护说明："
    echo "  - 衍生内容（derived: true）在后续 ingest 中视为二级来源"
    echo "  - ingest 不主动扫描 queries/ 目录"
    echo "  - 只有当用户明确要求时才读取 query 页面"
  fi
}

# 主入口
case "${1:-}" in
  check)
    if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
      log_error " 缺少参数"
      echo "用法: bash query-dedup.sh check '<主题>' <wiki_root>"
      exit 1
    fi
    check_duplicates "$2" "$3"
    ;;
  list)
    if [ -z "${2:-}" ]; then
      log_error " 缺少参数"
      echo "用法: bash query-dedup.sh list <wiki_root>"
      exit 1
    fi
    list_queries "$2"
    ;;
  stats)
    if [ -z "${2:-}" ]; then
      log_error " 缺少参数"
      echo "用法: bash query-dedup.sh stats <wiki_root>"
      exit 1
    fi
    stats_queries "$2"
    ;;
  *)
    echo "用法："
    echo "  bash query-dedup.sh check '<主题>' <wiki_root>   # 检查是否已有同主题 query 页面"
    echo "  bash query-dedup.sh list <wiki_root>             # 列出所有 query 页面"
    echo "  bash query-dedup.sh stats <wiki_root>            # 统计 query 页面"
    exit 1
    ;;
esac
