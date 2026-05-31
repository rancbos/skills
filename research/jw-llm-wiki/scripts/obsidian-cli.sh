#!/bin/bash
# obsidian-cli.sh — Obsidian CLI 集成包装脚本
# 用法：
#   bash obsidian-cli.sh read "<文件名>"           # 读取笔记
#   bash obsidian-cli.sh search "<关键词>"          # 搜索 vault
#   bash obsidian-cli.sh create "<文件名>" "<内容>" # 创建新笔记
#   bash obsidian-cli.sh append "<文件名>" "<内容>" # 追加内容到笔记
#   bash obsidian-cli.sh backlinks "<文件名>"       # 查看反向链接
#   bash obsidian-cli.sh tags                      # 标签统计
#   bash obsidian-cli.sh check                     # 检查 Obsidian CLI 是否可用
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u

# 检查 Obsidian CLI 是否可用
check_obsidian() {
  if command -v obsidian >/dev/null 2>&1; then
    echo "✅ Obsidian CLI 可用"
    obsidian --version 2>/dev/null || echo "版本未知"
    return 0
  else
    echo "❌ Obsidian CLI 不可用"
    echo ""
    echo "安装方法："
    echo "1. 确保 Obsidian 版本 >= 1.9.0"
    echo "2. 在 Obsidian 设置中启用 CLI"
    echo "3. 将 Obsidian 添加到 PATH"
    echo ""
    echo "或者使用 Obsidian URI 方案（不需要 CLI）"
    return 1
  fi
}

# 读取笔记
read_note() {
  local file="$1"
  
  if ! check_obsidian >/dev/null 2>&1; then
    log_error " Obsidian CLI 不可用"
    return 1
  fi
  
  echo "=== 读取笔记 ==="
  echo "文件: $file"
  echo ""
  
  obsidian read file="$file" 2>/dev/null || {
    log_error " 读取失败"
    return 1
  }
}

# 搜索 vault
search_vault() {
  local query="$1"
  local limit="${2:-10}"
  
  if ! check_obsidian >/dev/null 2>&1; then
    log_error " Obsidian CLI 不可用"
    return 1
  fi
  
  echo "=== 搜索 Vault ==="
  echo "关键词: $query"
  echo "限制: $limit"
  echo ""
  
  obsidian search query="$query" limit="$limit" 2>/dev/null || {
    log_error " 搜索失败"
    return 1
  }
}

# 创建新笔记
create_note() {
  local file="$1"
  local content="$2"
  
  if ! check_obsidian >/dev/null 2>&1; then
    log_error " Obsidian CLI 不可用"
    return 1
  fi
  
  echo "=== 创建笔记 ==="
  echo "文件: $file"
  echo ""
  
  obsidian create name="$file" content="$content" silent 2>/dev/null || {
    log_error " 创建失败"
    return 1
  }
  
  echo "✅ 笔记已创建"
}

# 追加内容到笔记
append_note() {
  local file="$1"
  local content="$2"
  
  if ! check_obsidian >/dev/null 2>&1; then
    log_error " Obsidian CLI 不可用"
    return 1
  fi
  
  echo "=== 追加内容 ==="
  echo "文件: $file"
  echo ""
  
  obsidian append file="$file" content="$content" 2>/dev/null || {
    log_error " 追加失败"
    return 1
  }
  
  echo "✅ 内容已追加"
}

# 查看反向链接
get_backlinks() {
  local file="$1"
  
  if ! check_obsidian >/dev/null 2>&1; then
    log_error " Obsidian CLI 不可用"
    return 1
  fi
  
  echo "=== 反向链接 ==="
  echo "文件: $file"
  echo ""
  
  obsidian backlinks file="$file" 2>/dev/null || {
    log_error " 获取反向链接失败"
    return 1
  }
}

# 标签统计
get_tags() {
  if ! check_obsidian >/dev/null 2>&1; then
    log_error " Obsidian CLI 不可用"
    return 1
  fi
  
  echo "=== 标签统计 ==="
  echo ""
  
  obsidian tags sort=count counts 2>/dev/null || {
    log_error " 获取标签失败"
    return 1
  }
}

# 主入口
case "${1:-}" in
  check)
    check_obsidian
    ;;
  read)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件名参数"
      exit 1
    fi
    read_note "$2"
    ;;
  search)
    if [ -z "${2:-}" ]; then
      log_error " 缺少关键词参数"
      exit 1
    fi
    search_vault "$2" "${3:-10}"
    ;;
  create)
    if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
      log_error " 缺少参数"
      echo "用法: bash obsidian-cli.sh create '<文件名>' '<内容>'"
      exit 1
    fi
    create_note "$2" "$3"
    ;;
  append)
    if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
      log_error " 缺少参数"
      echo "用法: bash obsidian-cli.sh append '<文件名>' '<内容>'"
      exit 1
    fi
    append_note "$2" "$3"
    ;;
  backlinks)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件名参数"
      exit 1
    fi
    get_backlinks "$2"
    ;;
  tags)
    get_tags
    ;;
  *)
    echo "用法："
    echo "  bash obsidian-cli.sh check                     # 检查 Obsidian CLI 是否可用"
    echo "  bash obsidian-cli.sh read '<文件名>'           # 读取笔记"
    echo "  bash obsidian-cli.sh search '<关键词>'          # 搜索 vault"
    echo "  bash obsidian-cli.sh create '<文件名>' '<内容>' # 创建新笔记"
    echo "  bash obsidian-cli.sh append '<文件名>' '<内容>' # 追加内容到笔记"
    echo "  bash obsidian-cli.sh backlinks '<文件名>'       # 查看反向链接"
    echo "  bash obsidian-cli.sh tags                      # 标签统计"
    exit 1
    ;;
esac
