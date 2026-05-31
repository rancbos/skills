#!/bin/bash
# cache.sh — Wiki 缓存管理脚本
# 用法：
#   bash cache.sh check "<raw文件路径>"    # 检查缓存状态
#   bash cache.sh update "<raw文件路径>"   # 更新缓存
#   bash cache.sh invalidate "<raw文件路径>" # 删除缓存
#   bash cache.sh status                   # 显示缓存状态
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

CACHE_FILE="$WIKI_ROOT/.wiki-cache.json"

# 确保缓存文件存在
ensure_cache() {
  if [ ! -f "$CACHE_FILE" ]; then
    echo "{}" > "$CACHE_FILE"
  fi
}

# 计算文件 hash（MD5）
compute_hash() {
  local file="$1"
  if [ -f "$file" ]; then
    md5sum "$file" 2>/dev/null | awk '{print $1}'
  else
    echo ""
  fi
}

# 获取文件元信息
get_file_meta() {
  local file="$1"
  if [ -f "$file" ]; then
    stat -c "%s %Y" "$file" 2>/dev/null || stat -f "%z %m" "$file" 2>/dev/null
  else
    echo "0 0"
  fi
}

# 检查缓存状态
check_cache() {
  local raw_file="$1"
  local abs_raw_file
  abs_raw_file=$(realpath "$raw_file" 2>/dev/null || echo "$raw_file")
  
  ensure_cache
  
  # 检查文件是否存在
  if [ ! -f "$abs_raw_file" ]; then
    echo "MISS:file_not_found"
    return 0
  fi
  
  # 计算当前 hash
  local current_hash
  current_hash=$(compute_hash "$abs_raw_file")
  
  if [ -z "$current_hash" ]; then
    echo "MISS:hash_error"
    return 0
  fi
  
  # 从缓存中读取（简单实现：用 grep 检查）
  local cached_hash
  cached_hash=$(grep -o "\"$abs_raw_file\"[^}]*\"hash\":\"[^\"]*\"" "$CACHE_FILE" 2>/dev/null | grep -o '"hash":"[^"]*"' | head -1 | sed 's/"hash":"//;s/"//')
  
  if [ -z "$cached_hash" ]; then
    echo "MISS:no_entry"
    return 0
  fi
  
  # 比较 hash
  if [ "$current_hash" = "$cached_hash" ]; then
    echo "HIT"
  else
    echo "MISS:hash_changed"
  fi
}

# 更新缓存
update_cache() {
  local raw_file="$1"
  local abs_raw_file
  abs_raw_file=$(realpath "$raw_file" 2>/dev/null || echo "$raw_file")
  
  ensure_cache
  
  # 计算当前 hash
  local current_hash
  current_hash=$(compute_hash "$abs_raw_file")
  
  if [ -z "$current_hash" ]; then
    log_error "无法计算文件 hash"
    return 1
  fi
  
  # 获取文件大小和修改时间
  local file_meta
  file_meta=$(get_file_meta "$abs_raw_file")
  local file_size=$(echo "$file_meta" | awk '{print $1}')
  local file_mtime=$(echo "$file_meta" | awk '{print $2}')
  
  # 简化实现：直接追加到缓存文件
  # 实际应该用 jq 来更新 JSON，这里用简单方法
  local temp_cache
  temp_cache=$(mktemp)
  
  # 读取现有缓存
  if [ -f "$CACHE_FILE" ]; then
    # 移除旧条目（如果存在）
    grep -v "\"$abs_raw_file\"" "$CACHE_FILE" > "$temp_cache" 2>/dev/null || true
  fi
  
  # 计算 source page 路径
  local source_page=""
  local wiki_sources_dir="$WIKI_ROOT/wiki/sources"
  if [ -d "$wiki_sources_dir" ]; then
    # 查找引用此 raw 文件的 source page
    source_page=$(grep -rl "$abs_raw_file" "$wiki_sources_dir" 2>/dev/null | head -1 || echo "")
  fi
  
  # 构建新条目
  local new_entry="  \"$abs_raw_file\": {"
  new_entry+="\"hash\":\"$current_hash\","
  new_entry+="\"size\":$file_size,"
  new_entry+="\"mtime\":$file_mtime,"
  new_entry+="\"updated\":\"$(date -Iseconds)\","
  new_entry+="\"source_page\":\"$source_page\""
  new_entry+="}"
  
  # 写入新缓存
  echo "{" > "$CACHE_FILE"
  # 添加现有条目（跳过开头的 { 和结尾的 }）
  if [ -s "$temp_cache" ]; then
    # 跳过第一行的 { 和最后一行的 }
    tail -n +2 "$temp_cache" | head -n -1 >> "$CACHE_FILE"
  fi
  # 添加新条目
  echo "$new_entry" >> "$CACHE_FILE"
  echo "}" >> "$CACHE_FILE"
  
  rm -f "$temp_cache"
  
  log_success " 缓存已更新"
  return 0
}

# 删除缓存条目
invalidate_cache() {
  local raw_file="$1"
  local abs_raw_file
  abs_raw_file=$(realpath "$raw_file" 2>/dev/null || echo "$raw_file")
  
  ensure_cache
  
  if [ ! -f "$CACHE_FILE" ]; then
    log_success " 缓存文件不存在，无需删除"
    return 0
  fi
  
  # 检查是否存在
  if ! grep -q "\"$abs_raw_file\"" "$CACHE_FILE" 2>/dev/null; then
    log_success " 缓存条目不存在"
    return 0
  fi
  
  # 删除条目
  local temp_cache
  temp_cache=$(mktemp)
  grep -v "\"$abs_raw_file\"" "$CACHE_FILE" > "$temp_cache"
  mv "$temp_cache" "$CACHE_FILE"
  
  log_success " 缓存已删除"
  return 0
}

# 显示缓存状态
show_status() {
  ensure_cache
  
  echo "=== Wiki 缓存状态 ==="
  echo "缓存文件：$CACHE_FILE"
  
  if [ ! -s "$CACHE_FILE" ] || [ "$(cat "$CACHE_FILE")" = "{}" ]; then
    echo "状态：空缓存"
    return 0
  fi
  
  # 统计条目数
  local entry_count
  entry_count=$(grep -c "\"hash\":" "$CACHE_FILE" 2>/dev/null || echo "0")
  echo "缓存条目：$entry_count"
  
  # 列出所有缓存的文件
  echo ""
  echo "缓存的 raw 文件："
  grep -o '"[^"]*": {' "$CACHE_FILE" 2>/dev/null | sed 's/": {//' | sed 's/^"//' | while read -r file; do
    if [ -f "$file" ]; then
      echo "  ✓ $file"
    else
      echo "  ✗ $file (文件不存在)"
    fi
  done
}

# 主入口
case "${1:-}" in
  check)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件路径参数"
      exit 1
    fi
    check_cache "$2"
    ;;
  update)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件路径参数"
      exit 1
    fi
    update_cache "$2"
    ;;
  invalidate)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件路径参数"
      exit 1
    fi
    invalidate_cache "$2"
    ;;
  status)
    show_status
    ;;
  *)
    echo "用法："
    echo "  bash cache.sh check <raw文件路径>     # 检查缓存状态"
    echo "  bash cache.sh update <raw文件路径>    # 更新缓存"
    echo "  bash cache.sh invalidate <raw文件路径> # 删除缓存"
    echo "  bash cache.sh status                  # 显示缓存状态"
    exit 1
    ;;
esac
