#!/bin/bash
# delete-helper.sh — 安全删除素材
# 用法：
#   bash delete-helper.sh scan "<文件路径>"       # 扫描删除影响
#   bash delete-helper.sh delete "<文件路径>"     # 安全删除
#   bash delete-helper.sh archive "<文件路径>"    # 归档而非删除
#   bash delete-helper.sh orphan                 # 列出孤儿页面
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

ARCHIVE_DIR="$WIKI_ROOT/_archive"

# 扫描删除影响
scan_impact() {
  local file="$1"
  
  if [ ! -f "$file" ]; then
    log_error " 文件不存在: $file"
    return 1
  fi
  
  local filename
  filename=$(basename "$file" .md)
  
  echo "=== 删除影响扫描 ==="
  echo "目标文件: $file"
  echo "文件名: $filename"
  echo ""
  
  # 1. 检查谁引用了这个文件
  echo "=== 引用此文件的页面 ==="
  local references
  references=$(grep -rl "\[\[${filename}\]\]" "$WIKI_ROOT/entities" "$WIKI_ROOT/concepts" 2>/dev/null | grep -v "$file")
  
  if [ -n "$references" ]; then
    local ref_count
    ref_count=$(echo "$references" | wc -l)
    echo "引用数量: $ref_count"
    echo ""
    echo "引用页面:"
    echo "$references" | while read -r ref; do
      echo "  - $ref"
    done
  else
    echo "无页面引用此文件"
  fi
  echo ""
  
  # 2. 检查此文件引用了谁
  echo "=== 此文件引用的页面 ==="
  local links
  links=$(grep -oP '\[\[([^\]]+)\]\]' "$file" 2>/dev/null | sed 's/\[\[//;s/\]\]//' | sort -u)
  
  if [ -n "$links" ]; then
    local link_count
    link_count=$(echo "$links" | wc -l)
    echo "引用数量: $link_count"
    echo ""
    echo "引用的页面:"
    echo "$links" | while read -r link; do
      # 检查目标是否存在
      local target_exists=false
      for dir in entities concepts comparisons queries; do
        if [ -f "$WIKI_ROOT/$dir/$link.md" ]; then
          target_exists=true
          break
        fi
      done
      
      if [ "$target_exists" = true ]; then
        echo "  - [[${link}]] ✓"
      else
        echo "  - [[${link}]] ✗ (目标不存在)"
      fi
    done
  else
    echo "此文件未引用其他页面"
  fi
  echo ""
  
  # 3. 检查 index.md 中是否有引用
  echo "=== index.md 引用 ==="
  if grep -q "$filename" "$WIKI_ROOT/index.md" 2>/dev/null; then
    echo "⚠️  index.md 中包含对此文件的引用"
    grep -n "$filename" "$WIKI_ROOT/index.md" | head -5 | while read -r line; do
      echo "  $line"
    done
  else
    echo "index.md 中无引用"
  fi
  echo ""
  
  # 4. 检查是否有 raw 文件关联
  echo "=== 关联 raw 文件 ==="
  local raw_refs
  raw_refs=$(grep -oP 'sources: \[([^\]]+)\]' "$file" 2>/dev/null | sed 's/sources: \[//;s/\]//')
  
  if [ -n "$raw_refs" ]; then
    echo "关联的 raw 文件:"
    echo "$raw_refs" | tr ',' '\n' | while read -r raw; do
      raw=$(echo "$raw" | xargs)  # 去除空格
      if [ -f "$WIKI_ROOT/$raw" ]; then
        echo "  - $raw ✓"
      else
        echo "  - $raw ✗ (文件不存在)"
      fi
    done
  else
    echo "无关联 raw 文件"
  fi
  echo ""
  
  # 5. 风险评估
  echo "=== 风险评估 ==="
  local risk_level="低"
  local risk_reasons=""
  
  if [ -n "$references" ]; then
    local ref_count
    ref_count=$(echo "$references" | wc -l)
    if [ "$ref_count" -gt 5 ]; then
      risk_level="高"
      risk_reasons="$risk_reasons 被 $ref_count 个页面引用"
    elif [ "$ref_count" -gt 0 ]; then
      risk_level="中"
      risk_reasons="$risk_reasons 被 $ref_count 个页面引用"
    fi
  fi
  
  if grep -q "$filename" "$WIKI_ROOT/index.md" 2>/dev/null; then
    if [ "$risk_level" = "低" ]; then
      risk_level="中"
    fi
    risk_reasons="$risk_reasons 在 index.md 中有引用"
  fi
  
  echo "风险级别: $risk_level"
  if [ -n "$risk_reasons" ]; then
    echo "风险原因: $risk_reasons"
  fi
  echo ""
  
  # 6. 建议
  echo "=== 建议 ==="
  if [ "$risk_level" = "高" ]; then
    echo "⚠️  高风险删除，建议："
    echo "1. 先修复所有引用此文件的页面"
    echo "2. 从 index.md 移除引用"
    echo "3. 考虑归档而非删除"
    echo "4. 如确认删除，使用: bash delete-helper.sh delete '$file'"
  elif [ "$risk_level" = "中" ]; then
    echo "⚠️  中风险删除，建议："
    echo "1. 检查引用页面是否需要更新"
    echo "2. 从 index.md 移除引用"
    echo "3. 考虑归档: bash delete-helper.sh archive '$file'"
    echo "4. 如确认删除，使用: bash delete-helper.sh delete '$file'"
  else
    echo "✅ 低风险删除，可以安全删除"
    echo "使用: bash delete-helper.sh delete '$file'"
  fi
}

# 安全删除
safe_delete() {
  local file="$1"
  
  if [ ! -f "$file" ]; then
    log_error " 文件不存在: $file"
    return 1
  fi
  
  local filename
  filename=$(basename "$file" .md)
  
  echo "=== 安全删除 ==="
  echo "目标文件: $file"
  echo ""
  
  # 1. 检查引用
  local references
  references=$(grep -rl "\[\[${filename}\]\]" "$WIKI_ROOT/entities" "$WIKI_ROOT/concepts" 2>/dev/null | grep -v "$file")
  
  if [ -n "$references" ]; then
    echo "⚠️  发现引用，需要先修复："
    echo "$references" | while read -r ref; do
      echo "  - $ref"
    done
    echo ""
    echo "请先修复引用，或使用归档: bash delete-helper.sh archive '$file'"
    return 1
  fi
  
  # 2. 从 index.md 移除
  if grep -q "$filename" "$WIKI_ROOT/index.md" 2>/dev/null; then
    echo "从 index.md 移除引用..."
    sed -i "/$filename/d" "$WIKI_ROOT/index.md"
  fi
  
  # 3. 删除文件
  echo "删除文件..."
  rm -f "$file"
  
  # 4. 检查是否需要删除父目录
  local parent_dir
  parent_dir=$(dirname "$file")
  if [ "$parent_dir" != "$WIKI_ROOT/entities" ] && [ "$parent_dir" != "$WIKI_ROOT/concepts" ]; then
    local dir_count
    dir_count=$(find "$parent_dir" -maxdepth 1 -name "*.md" -type f | wc -l)
    if [ "$dir_count" -eq 0 ]; then
      echo "删除空目录: $parent_dir"
      rmdir "$parent_dir" 2>/dev/null || true
    fi
  fi
  
  echo ""
  echo "✅ 删除完成"
  echo "已删除: $file"
}

# 归档而非删除
archive_file() {
  local file="$1"
  
  if [ ! -f "$file" ]; then
    log_error " 文件不存在: $file"
    return 1
  fi
  
  local filename
  filename=$(basename "$file" .md)
  
  # 确保归档目录存在
  mkdir -p "$ARCHIVE_DIR"
  
  # 保持目录结构
  local relative_path
  relative_path=$(realpath --relative-to="$WIKI_ROOT" "$file")
  local archive_path="$ARCHIVE_DIR/$relative_path"
  local archive_dir
  archive_dir=$(dirname "$archive_path")
  
  mkdir -p "$archive_dir"
  
  echo "=== 归档文件 ==="
  echo "原位置: $file"
  echo "归档位置: $archive_path"
  echo ""
  
  # 1. 移动文件
  mv "$file" "$archive_path"
  
  # 2. 更新 index.md（标记为已归档）
  if grep -q "$filename" "$WIKI_ROOT/index.md" 2>/dev/null; then
    echo "更新 index.md..."
    sed -i "s/\[\[${filename}\]\]/[已归档] ${filename}/g" "$WIKI_ROOT/index.md"
  fi
  
  # 3. 更新引用此文件的页面
  local references
  references=$(grep -rl "\[\[${filename}\]\]" "$WIKI_ROOT/entities" "$WIKI_ROOT/concepts" 2>/dev/null | grep -v "$archive_path")
  
  if [ -n "$references" ]; then
    echo "更新引用页面..."
    echo "$references" | while read -r ref; do
      sed -i "s/\[\[${filename}\]\]/[已归档] ${filename}/g" "$ref"
      echo "  - $ref"
    done
  fi
  
  echo ""
  echo "✅ 归档完成"
  echo "文件已移动到: $archive_path"
  echo "引用已更新为: [已归档] ${filename}"
}

# 列出孤儿页面
list_orphans() {
  echo "=== 孤儿页面 ==="
  echo ""
  
  local orphan_count=0
  local orphans=""
  
  # 收集所有 wikilinks
  local all_links=""
  while IFS= read -r -d '' file; do
    local links
    links=$(grep -oP '\[\[([^\]]+)\]\]' "$file" 2>/dev/null | sed 's/\[\[//;s/\]\]//')
    all_links="$all_links\n$links"
  done < <(find "$WIKI_ROOT/entities" "$WIKI_ROOT/concepts" -name "*.md" -type f -print0)
  
  # 检查每个页面是否被引用
  while IFS= read -r -d '' file; do
    local filename
    filename=$(basename "$file" .md)
    
    if ! echo "$all_links" | grep -q "$filename"; then
      orphan_count=$((orphan_count + 1))
      orphans="$orphans\n$file"
    fi
  done < <(find "$WIKI_ROOT/entities" "$WIKI_ROOT/concepts" -name "*.md" -type f -print0)
  
  echo "孤儿页面数量: $orphan_count"
  echo ""
  
  if [ "$orphan_count" -gt 0 ]; then
    echo "孤儿页面列表:"
    echo -e "$orphans" | sort | while read -r orphan; do
      if [ -n "$orphan" ]; then
        echo "  - $orphan"
      fi
    done
    echo ""
    echo "建议："
    echo "1. 为孤儿页面添加交叉引用"
    echo "2. 合并内容到相关页面"
    echo "3. 归档不再需要的页面"
  fi
}

# 主入口
case "${1:-}" in
  scan)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件路径参数"
      exit 1
    fi
    scan_impact "$2"
    ;;
  delete)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件路径参数"
      exit 1
    fi
    safe_delete "$2"
    ;;
  archive)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件路径参数"
      exit 1
    fi
    archive_file "$2"
    ;;
  orphan)
    list_orphans
    ;;
  *)
    echo "用法："
    echo "  bash delete-helper.sh scan <文件路径>       # 扫描删除影响"
    echo "  bash delete-helper.sh delete <文件路径>     # 安全删除"
    echo "  bash delete-helper.sh archive <文件路径>    # 归档而非删除"
    echo "  bash delete-helper.sh orphan               # 列出孤儿页面"
    exit 1
    ;;
esac
