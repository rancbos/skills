#!/bin/bash
# digest.sh — Digest 工作流辅助脚本
# 用法：
#   bash digest.sh search "<关键词>" <wiki_root>    # 搜索相关页面
#   bash digest.sh list "<主题>" <wiki_root>        # 列出将要综合的页面
#   bash digest.sh save "<主题>" "<格式>" <wiki_root> # 保存 digest 报告
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u

# 搜索相关页面
search_pages() {
  local keyword="$1"
  local wiki_root="$2"
  
  echo "=== 搜索相关页面 ==="
  echo "关键词: $keyword"
  echo ""
  
  # 别名展开
  local aliases=""
  if [ -f "$wiki_root/.wiki-aliases.json" ]; then
    aliases=$(jq -r "to_entries[] | select(.value[] | contains(\"$keyword\")) | .value[]" "$wiki_root/.wiki-aliases.json" 2>/dev/null | sort -u)
  fi
  
  # 合并关键词
  local all_keywords="$keyword"
  if [ -n "$aliases" ]; then
    all_keywords="$keyword
$aliases"
  fi
  
  echo "搜索关键词（含别名展开）:"
  echo "$all_keywords" | sed 's/^/  - /'
  echo ""
  
  # 搜索
  local results=""
  while read -r kw; do
    [ -z "$kw" ] && continue
    local found=$(grep -rl "$kw" "$wiki_root"/entities/ "$wiki_root"/concepts/ "$wiki_root"/comparisons/ 2>/dev/null)
    if [ -n "$found" ]; then
      results="$results
$found"
    fi
  done <<< "$all_keywords"
  
  # 去重
  results=$(echo "$results" | sort -u | grep -v '^$')
  
  if [ -z "$results" ]; then
    echo "未找到相关页面"
    return 1
  fi
  
  echo "找到的页面:"
  while read -r page; do
    [ -z "$page" ] && continue
    local basename=$(basename "$page" .md)
    local title=$(grep "^title:" "$page" 2>/dev/null | head -1 | sed 's/title: *//')
    local lines=$(wc -l < "$page" 2>/dev/null || echo "0")
    echo "  - $basename ($title, $lines 行)"
  done <<< "$results"
  
  echo ""
  echo "总计: $(echo "$results" | wc -l) 个页面"
}

# 列出将要综合的页面
list_pages() {
  local topic="$1"
  local wiki_root="$2"
  
  echo "=== 将要综合的页面 ==="
  echo "主题: $topic"
  echo ""
  
  # 搜索相关页面
  search_pages "$topic" "$wiki_root"
}

# 保存 digest 报告
save_digest() {
  local topic="$1"
  local format="$2"
  local wiki_root="$3"
  local date=$(date +%Y-%m-%d)
  
  # 确定文件名
  local filename=""
  case "$format" in
    deep)
      filename="${topic}-深度报告.md"
      ;;
    compare)
      filename="${topic}-对比.md"
      ;;
    timeline)
      filename="${topic}-时间线.md"
      ;;
    *)
      filename="${topic}-深度报告.md"
      ;;
  esac
  
  local filepath="$wiki_root/comparisons/$filename"
  
  echo "=== 保存 Digest 报告 ==="
  echo "主题: $topic"
  echo "格式: $format"
  echo "文件: $filepath"
  echo ""
  
  # 检查是否已存在
  if [ -f "$filepath" ]; then
    echo "⚠️  文件已存在: $filepath"
    echo "是否覆盖？(y/n)"
    read -r confirm
    if [ "$confirm" != "y" ]; then
      echo "取消保存"
      return 1
    fi
  fi
  
  # 创建目录
  mkdir -p "$wiki_root/comparisons"
  
  echo "文件已保存: $filepath"
  echo "请在对话中让 AI 填写报告内容。"
}

# 主入口
case "${1:-}" in
  search)
    if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
      log_error " 缺少参数"
      echo "用法: bash digest.sh search '<关键词>' <wiki_root>"
      exit 1
    fi
    search_pages "$2" "$3"
    ;;
  list)
    if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
      log_error " 缺少参数"
      echo "用法: bash digest.sh list '<主题>' <wiki_root>"
      exit 1
    fi
    list_pages "$2" "$3"
    ;;
  save)
    if [ -z "${2:-}" ] || [ -z "${3:-}" ] || [ -z "${4:-}" ]; then
      log_error " 缺少参数"
      echo "用法: bash digest.sh save '<主题>' '<格式>' <wiki_root>"
      exit 1
    fi
    save_digest "$2" "$3" "$4"
    ;;
  *)
    echo "用法："
    echo "  bash digest.sh search '<关键词>' <wiki_root>    # 搜索相关页面"
    echo "  bash digest.sh list '<主题>' <wiki_root>        # 列出将要综合的页面"
    echo "  bash digest.sh save '<主题>' '<格式>' <wiki_root> # 保存 digest 报告"
    echo ""
    echo "格式选项："
    echo "  deep      - 深度报告（默认）"
    echo "  compare   - 对比表"
    echo "  timeline  - 时间线"
    exit 1
    ;;
esac
