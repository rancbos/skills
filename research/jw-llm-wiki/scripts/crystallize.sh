#!/bin/bash
# crystallize.sh — 结晶化工作流：捕获对话中的洞见
# 用法：
#   bash crystallize.sh save "<洞见内容>" "<来源描述>"   # 保存洞见
#   bash crystallize.sh list                            # 列出待处理洞见
#   bash crystallize.sh process                         # 处理洞见（创建 wiki 页面）
#   bash crystallize.sh stats                           # 统计洞见数据
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

CRYSTALLIZE_DIR="$WIKI_ROOT/_crystallize"
PENDING_FILE="$CRYSTALLIZE_DIR/pending.md"
PROCESSED_FILE="$CRYSTALLIZE_DIR/processed.md"

# 确保目录和文件存在
mkdir -p "$CRYSTALLIZE_DIR"

if [ ! -f "$PENDING_FILE" ]; then
  cat > "$PENDING_FILE" << 'EOF'
# 待处理洞见

> 从对话中捕获的洞见，等待转化为 wiki 页面
> 格式：每条洞见以 `## [日期] 标题` 开头

EOF
fi

if [ ! -f "$PROCESSED_FILE" ]; then
  cat > "$PROCESSED_FILE" << 'EOF'
# 已处理洞见

> 已转化为 wiki 页面的洞见记录
> 格式：每条洞见以 `## [日期] 标题` 开头

EOF
fi

# 计算洞见数量的辅助函数
count_insights() {
  local file="$1"
  if [ ! -f "$file" ]; then
    echo "0"
    return
  fi
  local count
  count=$(grep -c "^## \[" "$file" 2>/dev/null) || count=0
  echo "$count"
}

# 保存洞见
save_insight() {
  local content="$1"
  local source="$2"
  local date=$(date +%Y-%m-%d)
  local time=$(date +%H:%M:%S)
  
  # 生成标题（取前20个字符）
  local title
  if [ ${#content} -gt 20 ]; then
    title="${content:0:20}..."
  else
    title="$content"
  fi
  
  # 写入待处理文件
  cat >> "$PENDING_FILE" << EOF

## [$date] $title

**来源**: $source
**时间**: $date $time
**内容**:
$content

**状态**: 待处理
EOF
  
  echo "✅ 洞见已保存"
  echo "标题: $title"
  echo "来源: $source"
  echo "位置: $PENDING_FILE"
}

# 列出待处理洞见
list_pending() {
  echo "=== 待处理洞见 ==="
  echo ""
  
  local count
  count=$(count_insights "$PENDING_FILE")
  echo "待处理数量: $count"
  echo ""
  
  if [ "$count" -eq 0 ]; then
    echo "暂无待处理洞见"
    return 0
  fi
  
  # 显示洞见列表
  grep "^## \[" "$PENDING_FILE" | while read -r line; do
    echo "  $line"
  done
}

# 处理洞见
process_insights() {
  echo "=== 处理洞见 ==="
  echo ""
  
  local count
  count=$(count_insights "$PENDING_FILE")
  echo "待处理数量: $count"
  echo ""
  
  if [ "$count" -eq 0 ]; then
    echo "暂无待处理洞见"
    return 0
  fi
  
  # 提示用户
  echo "处理流程："
  echo "1. 读取每条洞见"
  echo "2. 判断是否值得创建 wiki 页面"
  echo "3. 如果是，创建页面并更新 index.md"
  echo "4. 将洞见移动到已处理文件"
  echo ""
  echo "请在对话中告诉我要处理哪些洞见，例如："
  echo "  '处理第一条洞见'"
  echo "  '处理关于 X 的洞见'"
  echo ""
  
  # 显示洞见内容
  echo "=== 洞见详情 ==="
  cat "$PENDING_FILE"
}

# 统计洞见数据
show_stats() {
  echo "=== 洞见统计 ==="
  echo ""
  
  local pending_count
  pending_count=$(count_insights "$PENDING_FILE")
  echo "待处理: $pending_count"
  
  local processed_count
  processed_count=$(count_insights "$PROCESSED_FILE")
  echo "已处理: $processed_count"
  
  local total=$((pending_count + processed_count))
  echo "总计: $total"
  echo ""
  
  # 转化率
  if [ "$total" -gt 0 ]; then
    local rate=$((processed_count * 100 / total))
    echo "转化率: $rate%"
  fi
  
  echo ""
  echo "=== 最近洞见 ==="
  # 显示最近5条洞见
  grep "^## \[" "$PENDING_FILE" | tail -5 | while read -r line; do
    echo "  $line"
  done
}

# 标记洞见为已处理
mark_processed() {
  local title="$1"
  
  # 从待处理文件中提取洞见
  local insight
  insight=$(sed -n "/^## .*${title}/,/^## \[/p" "$PENDING_FILE" | head -n -1)
  
  if [ -z "$insight" ]; then
    log_error " 未找到匹配的洞见: $title"
    return 1
  fi
  
  # 添加到已处理文件
  echo "$insight" >> "$PROCESSED_FILE"
  
  # 从待处理文件中删除
  sed -i "/^## .*${title}/,/^## \[/d" "$PENDING_FILE"
  
  echo "✅ 洞见已标记为已处理: $title"
}

# 主入口
case "${1:-}" in
  save)
    if [ -z "${2:-}" ] || [ -z "${3:-}" ]; then
      log_error " 缺少参数"
      echo "用法: bash crystallize.sh save '<洞见内容>' '<来源描述>'"
      exit 1
    fi
    save_insight "$2" "$3"
    ;;
  list)
    list_pending
    ;;
  process)
    process_insights
    ;;
  stats)
    show_stats
    ;;
  mark)
    if [ -z "${2:-}" ]; then
      log_error " 缺少标题参数"
      exit 1
    fi
    mark_processed "$2"
    ;;
  *)
    echo "用法："
    echo "  bash crystallize.sh save '<洞见内容>' '<来源描述>'  # 保存洞见"
    echo "  bash crystallize.sh list                            # 列出待处理洞见"
    echo "  bash crystallize.sh process                         # 处理洞见"
    echo "  bash crystallize.sh stats                           # 统计洞见数据"
    echo "  bash crystallize.sh mark '<标题>'                   # 标记为已处理"
    exit 1
    ;;
esac
