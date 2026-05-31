#!/bin/bash
# content-grading.sh — 素材内容分级处理
# 用法：
#   bash content-grading.sh grade "<文件路径>"    # 判断处理级别
#   bash content-grading.sh stats "<目录路径>"    # 统计目录内素材分级
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

# 分级阈值
THRESHOLD_FULL=1000     # >1000字：完整处理
THRESHOLD_MEDIUM=300    # 300-1000字：标准处理
# <300字：简化处理

# 判断处理级别
grade_content() {
  local file="$1"
  
  if [ ! -f "$file" ]; then
    log_error " 文件不存在: $file"
    return 1
  fi
  
  # 统计字数（中文按字符计，英文按单词计）
  local char_count
  char_count=$(wc -m < "$file" 2>/dev/null || echo "0")
  
  # 统计行数
  local line_count
  line_count=$(wc -l < "$file" 2>/dev/null || echo "0")
  
  # 判断级别
  local level
  local description
  local token_estimate
  
  if [ "$char_count" -gt "$THRESHOLD_FULL" ]; then
    level="full"
    description="完整处理：提取实体、概念、交叉引用、置信度标注"
    token_estimate="~3000-5000 tokens"
  elif [ "$char_count" -gt "$THRESHOLD_MEDIUM" ]; then
    level="standard"
    description="标准处理：提取核心实体和概念，基本交叉引用"
    token_estimate="~1500-3000 tokens"
  else
    level="simple"
    description="简化处理：仅提取关键信息，合并到已有页面或创建简短页面"
    token_estimate="~500-1500 tokens"
  fi
  
  # 输出结果
  echo "=== 内容分级 ==="
  echo "文件: $file"
  echo "字符数: $char_count"
  echo "行数: $line_count"
  echo "处理级别: $level"
  echo "说明: $description"
  echo "预估 token: $token_estimate"
  echo ""
  echo "=== 处理建议 ==="
  
  case "$level" in
    full)
      echo "1. 完整提取所有实体和概念"
      echo "2. 创建独立 wiki 页面（每个实体/概念一页）"
      echo "3. 建立完整交叉引用（每页至少 2 个出链）"
      echo "4. 标注置信度（EXTRACTED/INFERRED/AMBIGUOUS/UNVERIFIED）"
      echo "5. 添加来源标记（^[raw/...]）"
      echo "6. 更新 index.md 和 log.md"
      ;;
    standard)
      echo "1. 提取核心实体（3-5个）和关键概念"
      echo "2. 创建独立页面或更新已有页面"
      echo "3. 建立基本交叉引用"
      echo "4. 标注置信度"
      echo "5. 更新 index.md 和 log.md"
      ;;
    simple)
      echo "1. 提取 1-2 个关键信息点"
      echo "2. 优先合并到已有页面（而非创建新页面）"
      echo "3. 如需创建页面，保持简洁（<50行）"
      echo "4. 简化交叉引用"
      echo "5. 更新 index.md 和 log.md"
      ;;
  esac
}

# 统计目录内素材分级
stats_directory() {
  local dir="$1"
  
  if [ ! -d "$dir" ]; then
    log_error " 目录不存在: $dir"
    return 1
  fi
  
  echo "=== 素材分级统计 ==="
  echo "目录: $dir"
  echo ""
  
  local full_count=0
  local standard_count=0
  local simple_count=0
  local total_files=0
  local total_chars=0
  
  # 遍历所有文件
  while IFS= read -r -d '' file; do
    # 跳过非文本文件
    if file --mime-type "$file" 2>/dev/null | grep -q "text/"; then
      local char_count
      char_count=$(wc -m < "$file" 2>/dev/null || echo "0")
      
      total_files=$((total_files + 1))
      total_chars=$((total_chars + char_count))
      
      if [ "$char_count" -gt "$THRESHOLD_FULL" ]; then
        full_count=$((full_count + 1))
      elif [ "$char_count" -gt "$THRESHOLD_MEDIUM" ]; then
        standard_count=$((standard_count + 1))
      else
        simple_count=$((simple_count + 1))
      fi
    fi
  done < <(find "$dir" -type f -print0)
  
  echo "文件总数: $total_files"
  echo "总字符数: $total_chars"
  echo ""
  echo "分级统计:"
  echo "  完整处理 (>1000字): $full_count 文件"
  echo "  标准处理 (300-1000字): $standard_count 文件"
  echo "  简化处理 (<300字): $simple_count 文件"
  echo ""
  
  # 计算 token 节省
  local token_full=$((full_count * 4000))
  local token_standard=$((standard_count * 2000))
  local token_simple=$((simple_count * 1000))
  local token_total=$((token_full + token_standard + token_simple))
  local token_uniform=$((total_files * 4000))
  local token_saved=$((token_uniform - token_total))
  
  echo "=== Token 效率 ==="
  echo "统一处理预估: $token_uniform tokens"
  echo "分级处理预估: $token_total tokens"
  echo "节省: $token_saved tokens ($(( token_saved * 100 / token_uniform ))%)"
}

# 主入口
case "${1:-}" in
  grade)
    if [ -z "${2:-}" ]; then
      log_error " 缺少文件路径参数"
      exit 1
    fi
    grade_content "$2"
    ;;
  stats)
    if [ -z "${2:-}" ]; then
      log_error " 缺少目录路径参数"
      exit 1
    fi
    stats_directory "$2"
    ;;
  *)
    echo "用法："
    echo "  bash content-grading.sh grade <文件路径>    # 判断处理级别"
    echo "  bash content-grading.sh stats <目录路径>    # 统计目录内素材分级"
    exit 1
    ;;
esac
