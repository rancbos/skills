#!/bin/bash
# create-source-page.sh — 原子写入 source 页面 + 自动更新缓存
# 用法：bash create-source-page.sh <raw_file> <output_path> <content_file>
#
# 功能：
# 1. 原子写入：临时文件 + rename，防止写一半崩溃
# 2. 自动更新缓存：写入成功后自动更新 .wiki-cache.json
# 3. 失败回滚：缓存更新失败时回滚已写入的文件
#
# 参数：
#   raw_file     : 原始素材文件路径（绝对或相对路径）
#   output_path  : 目标页面路径（相对于知识库根目录，如 entities/invest/xxx.md）
#   content_file : 包含待写入内容的临时文件路径

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

usage() {
  cat <<'EOF'
用法：
  bash create-source-page.sh <raw_file> <output_path> <content_file>

参数：
  raw_file     : 原始素材文件路径
  output_path  : 目标页面路径（相对于知识库根目录）
  content_file : 包含待写入内容的临时文件路径
EOF
}

# 参数校验
if [ "$#" -ne 3 ]; then
  usage
  exit 1
fi

raw_file="$1"
output_path="$2"
content_file="$3"

# raw_file 和 content_file 必须存在
if [ ! -f "$raw_file" ]; then
  log_error " 原始素材文件不存在：$raw_file"
  exit 1
fi

if [ ! -f "$content_file" ]; then
  log_error " 内容文件不存在：$content_file"
  exit 1
fi

# 查找知识库根目录
find_wiki_root() {
  local file_path="$1"
  local dir parent

  dir="$(cd "$(dirname "$file_path")" && pwd)"

  while true; do
    if [ -f "$dir/.wiki-cache.json" ] || [ -f "$dir/.wiki-schema.md" ] || [ -f "$dir/SCHEMA.md" ]; then
      printf '%s\n' "$dir"
      return 0
    fi

    parent="$(dirname "$dir")"
    [ "$parent" = "$dir" ] && return 1
    dir="$parent"
  done
}

wiki_root="$(find_wiki_root "$raw_file")" || {
  log_error " 未找到知识库根目录：$raw_file"
  exit 1
}

# 拼接完整目标路径
full_output="$wiki_root/$output_path"

# 确保目标目录存在
mkdir -p "$(dirname "$full_output")"

# 第一步：原子写入（临时文件 + rename，防止写一半崩溃）
tmp_output="${full_output}.tmp.$$"
if ! cp "$content_file" "$tmp_output"; then
  rm -f "$tmp_output" 2>/dev/null || true
  log_error " 写入临时文件失败"
  exit 1
fi

if ! mv "$tmp_output" "$full_output"; then
  rm -f "$tmp_output" 2>/dev/null || true
  log_error " 原子重命名失败"
  exit 1
fi

# 第二步：更新缓存
if [ -f "$SCRIPT_DIR/cache.sh" ]; then
  if ! bash "$SCRIPT_DIR/cache.sh" update "$raw_file"; then
    # 缓存更新失败 → 回滚：删除已写入的文件
    rm -f "$full_output"
    log_error " 缓存更新失败，已回滚写入"
    exit 1
  fi
fi

log_success "$output_path"
exit 0
