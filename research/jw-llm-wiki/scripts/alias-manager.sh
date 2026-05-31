#!/bin/bash
# alias-manager.sh — 别名管理脚本
# 用法：
#   bash alias-manager.sh list                    # 列出所有别名组
#   bash alias-manager.sh get "<关键词>"         # 获取关键词的别名组
#   bash alias-manager.sh add "<组名>" "<词1>" "<词2>" ...  # 添加别名组
#   bash alias-manager.sh expand "<关键词>"       # 展开关键词的所有别名
#   bash alias-manager.sh search "<关键词>"       # 搜索时使用别名展开
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u

# 自动检测 WIKI_ROOT
# 检测 Wiki 根目录
WIKI_ROOT=$(detect_wiki_root "${1:-}")
if [ -z "$WIKI_ROOT" ]; then
  log_error "未找到知识库。请设置 WIKI_PATH 环境变量或先运行 init。"
  exit 1
fi

ALIAS_FILE="$WIKI_ROOT/.wiki-aliases.json"

# 确保别名文件存在
ensure_alias_file() {
  if [ ! -f "$ALIAS_FILE" ]; then
    echo "{}" > "$ALIAS_FILE"
  fi
}

# 列出所有别名组
list_aliases() {
  ensure_alias_file
  
  if [ ! -s "$ALIAS_FILE" ] || [ "$(cat "$ALIAS_FILE")" = "{}" ]; then
    echo "暂无别名组"
    return 0
  fi
  
  echo "=== 别名组列表 ==="
  # 简单解析 JSON（不依赖 jq）
  grep -o '"[^"]*":' "$ALIAS_FILE" | sed 's/":.*//' | sed 's/^"//' | while read -r group; do
    echo "  - $group"
  done
}

# 获取关键词的别名组
get_alias_group() {
  local keyword="$1"
  ensure_alias_file
  
  # 查找包含该关键词的别名组
  local found=0
  while IFS= read -r line; do
    # 提取组名
    local group_name=$(echo "$line" | sed 's/":.*//' | sed 's/^"//')
    # 检查是否包含关键词
    if echo "$line" | grep -q "\"$keyword\""; then
      echo "$group_name"
      found=1
    fi
  done < <(grep '":' "$ALIAS_FILE" 2>/dev/null)
  
  if [ $found -eq 0 ]; then
    echo "未找到包含 '$keyword' 的别名组"
  fi
}

# 添加别名组
add_alias_group() {
  local group_name="$1"
  shift
  local words=("$@")
  
  ensure_alias_file
  
  # 构建新的别名组 JSON
  local new_group="  \"$group_name\": ["
  local first=1
  for word in "${words[@]}"; do
    if [ $first -eq 1 ]; then
      new_group+="\"$word\""
      first=0
    else
      new_group+=", \"$word\""
    fi
  done
  new_group+="]"
  
  # 读取现有内容
  local temp_file
  temp_file=$(mktemp)
  
  if [ -s "$ALIAS_FILE" ] && [ "$(cat "$ALIAS_FILE")" != "{}" ]; then
    # 移除旧的同名组（如果存在）
    grep -v "\"$group_name\":" "$ALIAS_FILE" > "$temp_file" 2>/dev/null || true
    
    # 添加新组
    # 移除最后的 }
    sed -i '$ s/}$//' "$temp_file"
    # 添加逗号（如果文件不为空）
    if [ -s "$temp_file" ]; then
      echo "," >> "$temp_file"
    fi
    echo "$new_group" >> "$temp_file"
    echo "}" >> "$temp_file"
  else
    echo "{" > "$temp_file"
    echo "$new_group" >> "$temp_file"
    echo "}" >> "$temp_file"
  fi
  
  mv "$temp_file" "$ALIAS_FILE"
  log_success "别名组 '$group_name' 已添加"
}

# 展开关键词的所有别名
expand_keyword() {
  local keyword="$1"
  ensure_alias_file
  
  # 查找包含该关键词的别名组
  local aliases=()
  while IFS= read -r line; do
    # 提取别名列表
    local alias_list=$(echo "$line" | grep -o '\[.*\]' | sed 's/\[//;s/\]//;s/"//g;s/,/ /g')
    for alias in $alias_list; do
      aliases+=("$alias")
    done
  done < <(grep "\"$keyword\"" "$ALIAS_FILE" 2>/dev/null)
  
  if [ ${#aliases[@]} -eq 0 ]; then
    echo "$keyword"
  else
    # 去重并输出
    printf "%s\n" "${aliases[@]}" | sort -u | tr '\n' ' '
  fi
}

# 搜索时使用别名展开
search_with_aliases() {
  local keyword="$1"
  local wiki_dir="$WIKI_ROOT"
  
  # 展开关键词
  local expanded_keywords
  expanded_keywords=$(expand_keyword "$keyword")
  
  echo "搜索关键词：$keyword"
  echo "展开后：$expanded_keywords"
  echo ""
  
  # 搜索所有展开的关键词
  for kw in $expanded_keywords; do
    local count=$(grep -rl "$kw" "$wiki_dir"/*.md 2>/dev/null | wc -l)
    if [ $count -gt 0 ]; then
      echo "  '$kw'：找到 $count 个页面"
    fi
  done
}

# 主入口
case "${1:-}" in
  list)
    list_aliases
    ;;
  get)
    if [ -z "${2:-}" ]; then
      log_error " 缺少关键词参数"
      exit 1
    fi
    get_alias_group "$2"
    ;;
  add)
    if [ $# -lt 3 ]; then
      log_error " 缺少参数"
      echo "用法：bash alias-manager.sh add \"<组名>\" \"<词1>\" \"<词2>\" ..."
      exit 1
    fi
    add_alias_group "${@:2}"
    ;;
  expand)
    if [ -z "${2:-}" ]; then
      log_error " 缺少关键词参数"
      exit 1
    fi
    expand_keyword "$2"
    ;;
  search)
    if [ -z "${2:-}" ]; then
      log_error " 缺少关键词参数"
      exit 1
    fi
    search_with_aliases "$2"
    ;;
  *)
    echo "用法："
    echo "  bash alias-manager.sh list                    # 列出所有别名组"
    echo "  bash alias-manager.sh get \"<关键词>\"         # 获取关键词的别名组"
    echo "  bash alias-manager.sh add \"<组名>\" \"<词1>\" \"<词2>\" ...  # 添加别名组"
    echo "  bash alias-manager.sh expand \"<关键词>\"       # 展开关键词的所有别名"
    echo "  bash alias-manager.sh search \"<关键词>\"       # 搜索时使用别名展开"
    exit 1
    ;;
esac
