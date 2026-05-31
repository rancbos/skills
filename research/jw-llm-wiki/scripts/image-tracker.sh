#!/bin/bash
# image-tracker.sh — 图片追踪
# 用法：
#   bash image-tracker.sh scan "<文件路径>"     # 扫描单个文件
#   bash image-tracker.sh scan-dir "<目录路径>" # 扫描整个目录
#   bash image-tracker.sh report               # 显示扫描报告
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

REPORT_FILE="$WIKI_ROOT/.image-tracker-report.txt"

# 图片引用模式
IMAGE_PATTERNS=(
  '!\['                    # Markdown 图片 ![alt](url)
  '<img'                   # HTML 图片 <img src="...">
  '\.png'                  # PNG 文件
  '\.jpg'                  # JPG 文件
  '\.jpeg'                 # JPEG 文件
  '\.gif'                  # GIF 文件
  '\.svg'                  # SVG 文件
  '\.webp'                 # WebP 文件
)

# 扫描单个文件
scan_file() {
  local file="$1"
  local findings=""
  local total_matches=0
  
  if [ ! -f "$file" ]; then
    log_error " 文件不存在: $file"
    return 1
  fi
  
  echo "=== 图片追踪 ==="
  echo "文件: $file"
  echo ""
  
  # 遍历所有模式
  for pattern in "${IMAGE_PATTERNS[@]}"; do
    local matches
    matches=$(grep -c "$pattern" "$file" 2>/dev/null || true)
    matches=${matches:-0}
    
    if [ "$matches" -gt 0 ]; then
      echo "  $pattern: $matches 处"
      # 显示匹配内容
      grep -n "$pattern" "$file" 2>/dev/null | head -3 | while read -r line; do
        echo "    $line"
      done
      total_matches=$((total_matches + matches))
      findings="$findings\n$pattern: $matches 处"
    fi
  done
  
  echo ""
  if [ "$total_matches" -eq 0 ]; then
    echo "✅ 未发现图片引用"
  else
    echo "⚠️  发现 $total_matches 处图片引用"
    echo ""
    echo "建议："
    echo "1. 检查图片链接是否有效"
    echo "2. 下载图片到 raw/assets/ 目录"
    echo "3. 更新 source 页面的 image_paths 字段"
  fi
  
  # 记录到报告
  echo "=== $file ===" >> "$REPORT_FILE"
  echo -e "$findings" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
}

# 扫描目录
scan_directory() {
  local dir="$1"
  
  if [ ! -d "$dir" ]; then
    log_error " 目录不存在: $dir"
    return 1
  fi
  
  echo "=== 图片追踪（目录） ==="
  echo "目录: $dir"
  echo ""
  
  # 初始化报告
  echo "图片追踪报告 - $(date)" > "$REPORT_FILE"
  echo "目录: $dir" >> "$REPORT_FILE"
  echo "======================================" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  
  local total_files=0
  local files_with_images=0
  local total_images=0
  
  # 遍历所有文件
  while IFS= read -r -d '' file; do
    # 跳过非文本文件
    if file --mime-type "$file" 2>/dev/null | grep -q "text/"; then
      total_files=$((total_files + 1))
      
      # 扫描文件
      local file_images=0
      for pattern in "${IMAGE_PATTERNS[@]}"; do
        local matches
        matches=$(grep -c "$pattern" "$file" 2>/dev/null || true)
        matches=${matches:-0}
        file_images=$((file_images + matches))
      done
      
      if [ "$file_images" -gt 0 ]; then
        files_with_images=$((files_with_images + 1))
        total_images=$((total_images + file_images))
        echo "  $(basename "$file"): $file_images 处图片引用"
      fi
    fi
  done < <(find "$dir" -type f -name "*.md" -print0)
  
  echo ""
  echo "=== 扫描统计 ==="
  echo "扫描文件数: $total_files"
  echo "有图片文件: $files_with_images"
  echo "图片引用总数: $total_images"
  echo ""
  
  if [ "$total_images" -eq 0 ]; then
    echo "✅ 未发现图片引用"
  else
    echo "⚠️  发现图片引用，详见报告: $REPORT_FILE"
    echo ""
    echo "建议："
    echo "1. 检查图片链接是否有效"
    echo "2. 下载图片到 raw/assets/ 目录"
    echo "3. 更新 source 页面的 image_paths 字段"
  fi
}

# 显示报告
show_report() {
  if [ ! -f "$REPORT_FILE" ]; then
    echo "未找到扫描报告，请先运行 scan 或 scan-dir"
    return 1
  fi
  cat "$REPORT_FILE"
}

# 主入口
case "${1:-}" in
  scan)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件路径参数"
      exit 1
    fi
    scan_file "$2"
    ;;
  scan-dir)
    if [ -z "${2:-}" ]; then
      log_error " 缺少目录路径参数"
      exit 1
    fi
    scan_directory "$2"
    ;;
  report)
    show_report
    ;;
  *)
    echo "用法："
    echo "  bash image-tracker.sh scan <文件路径>     # 扫描单个文件"
    echo "  bash image-tracker.sh scan-dir <目录路径> # 扫描整个目录"
    echo "  bash image-tracker.sh report              # 显示扫描报告"
    exit 1
    ;;
esac
