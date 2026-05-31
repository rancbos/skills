#!/bin/bash
# common.sh — 共享工具库
# 所有 jw-llm-wiki 脚本都应该 source 这个文件
# 用法: SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; source "$SCRIPT_DIR/lib/common.sh"

set -u

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

log_verbose() {
  if [ "${VERBOSE:-false}" = true ]; then
    echo -e "  [verbose] $1"
  fi
}

# 检测 Wiki 根目录
# 优先级: 参数 > WIKI_PATH 环境变量 > ~/.llm-wiki-path 文件 > 当前目录
detect_wiki_root() {
  local override="${1:-}"
  
  if [ -n "$override" ] && [ -d "$override" ]; then
    echo "$override"
    return 0
  fi
  
  if [ -n "${WIKI_PATH:-}" ] && [ -d "$WIKI_PATH" ]; then
    echo "$WIKI_PATH"
    return 0
  fi
  
  if [ -f "$HOME/.llm-wiki-path" ]; then
    local stored_path
    stored_path=$(cat "$HOME/.llm-wiki-path" 2>/dev/null)
    if [ -n "$stored_path" ] && [ -d "$stored_path" ]; then
      echo "$stored_path"
      return 0
    fi
  fi
  
  # 检查当前目录
  if [ -f "./SCHEMA.md" ] || [ -f "./.wiki-schema.md" ]; then
    echo "$(pwd)"
    return 0
  fi
  
  return 1
}

# 验证 Wiki 目录结构
validate_wiki_root() {
  local wiki_root="$1"
  
  if [ ! -d "$wiki_root" ]; then
    log_error "Wiki 目录不存在: $wiki_root"
    return 1
  fi
  
  if [ ! -d "$wiki_root/entities" ]; then
    log_error "entities 目录不存在: $wiki_root/entities"
    return 1
  fi
  
  if [ ! -f "$wiki_root/index.md" ]; then
    log_warn "index.md 不存在: $wiki_root/index.md"
  fi
  
  return 0
}

# 检查依赖工具
check_dependency() {
  local cmd="$1"
  local package="${2:-$cmd}"
  
  if ! command -v "$cmd" >/dev/null 2>&1; then
    log_error "$cmd 未安装。请运行: apt install $package"
    return 1
  fi
  return 0
}

# 安全的 grep -c 替代（避免 "0\n0" 问题）
safe_grep_count() {
  local pattern="$1"
  local file="$2"
  local count
  count=$(grep -c "$pattern" "$file" 2>/dev/null || true)
  echo "${count:-0}"
}

# 原子写入文件
atomic_write() {
  local target="$1"
  local content_file="$2"
  local tmp="${target}.tmp.$$"
  
  if ! cp "$content_file" "$tmp"; then
    rm -f "$tmp" 2>/dev/null || true
    log_error "写入临时文件失败: $tmp"
    return 1
  fi
  
  if ! mv "$tmp" "$target"; then
    rm -f "$tmp" 2>/dev/null || true
    log_error "原子重命名失败: $tmp -> $target"
    return 1
  fi
  
  return 0
}

# 使用方法提示
usage_header() {
  local script_name="$1"
  local description="$2"
  
  echo "=== $script_name ==="
  echo "$description"
  echo ""
}

# 导出变量
export SKILL_DIR="${SKILL_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export SCRIPTS_DIR="$SKILL_DIR/scripts"
export LIB_DIR="$SKILL_DIR/scripts/lib"
