#!/bin/bash
# privacy-check.sh — 隐私信息自查
# 用法：
#   bash privacy-check.sh scan "<文件路径>"     # 扫描单个文件
#   bash privacy-check.sh scan-dir "<目录路径>" # 扫描整个目录
#   bash privacy-check.sh report               # 显示扫描报告
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

REPORT_FILE="$WIKI_ROOT/.privacy-scan-report.txt"

# 隐私模式定义
declare -A PATTERNS
PATTERNS=(
  ["手机号"]="1[3-9][0-9]{9}"
  ["身份证号"]="[1-9][0-9]{5}(19|20)[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[0-9]{3}[0-9Xx]"
  ["邮箱地址"]="[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
  ["银行卡号"]="[0-9]{16,19}"
  ["API密钥"]="(sk|ak|key|token|secret|password)[_-]?[=:\"' ]+[a-zA-Z0-9]{20,}"
  ["IP地址"]="([0-9]{1,3}\.){3}[0-9]{1,3}"
  ["URL参数中的敏感信息"]="[?&](key|token|secret|password|api_key)=[^&]+"
  ["SSH私钥"]="-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"
  ["JWT令牌"]="eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*"
  ["AWS密钥"]="AKIA[0-9A-Z]{16}"
  ["GitHub Token"]="gh[ps]_[A-Za-z0-9_]{36,}"
  ["OpenAI Key"]="sk-[a-zA-Z0-9]{48,}"
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
  
  echo "=== 隐私扫描 ==="
  echo "文件: $file"
  echo ""
  
  # 遍历所有模式
  for category in "${!PATTERNS[@]}"; do
    local pattern="${PATTERNS[$category]}"
    local matches
    matches=$(grep -cP "$pattern" "$file" 2>/dev/null | wc -l)
    
    if [ "$matches" -gt 0 ]; then
      echo "⚠️  $category: $matches 处"
      # 显示匹配内容（脱敏）
      grep -oP "$pattern" "$file" 2>/dev/null | head -3 | while read -r match; do
        # 脱敏显示
        local len=${#match}
        if [ "$len" -gt 8 ]; then
          local masked="${match:0:4}****${match: -4}"
          echo "    示例: $masked"
        else
          echo "    示例: ****"
        fi
      done
      total_matches=$((total_matches + matches))
      findings="$findings\n$category: $matches 处"
    fi
  done
  
  echo ""
  if [ "$total_matches" -eq 0 ]; then
    echo "✅ 未发现隐私信息"
  else
    echo "⚠️  发现 $total_matches 处潜在隐私信息"
    echo ""
    echo "建议："
    echo "1. 检查是否为真实个人信息"
    echo "2. 如为示例数据，考虑脱敏后存储"
    echo "3. 如为敏感信息，移除或加密存储"
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
  
  echo "=== 隐私扫描（目录） ==="
  echo "目录: $dir"
  echo ""
  
  # 初始化报告
  echo "隐私扫描报告 - $(date)" > "$REPORT_FILE"
  echo "目录: $dir" >> "$REPORT_FILE"
  echo "======================================" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  
  local total_files=0
  local files_with_issues=0
  local total_issues=0
  
  # 遍历所有文件
  while IFS= read -r -d '' file; do
    # 跳过非文本文件
    if file --mime-type "$file" 2>/dev/null | grep -q "text/"; then
      total_files=$((total_files + 1))
      
      # 扫描文件
      local file_issues=0
      for category in "${!PATTERNS[@]}"; do
        local pattern="${PATTERNS[$category]}"
        local matches
        matches=$(grep -cP "$pattern" "$file" 2>/dev/null | wc -l)
        if [ "$matches" -gt 0 ]; then
          file_issues=$((file_issues + matches))
        fi
      done
      
      if [ "$file_issues" -gt 0 ]; then
        files_with_issues=$((files_with_issues + 1))
        total_issues=$((total_issues + file_issues))
        echo "⚠️  $file ($file_issues 处)"
      fi
    fi
  done < <(find "$dir" -type f -print0)
  
  echo ""
  echo "=== 扫描统计 ==="
  echo "扫描文件数: $total_files"
  echo "有问题文件: $files_with_issues"
  echo "问题总数: $total_issues"
  echo ""
  
  if [ "$total_issues" -eq 0 ]; then
    echo "✅ 未发现隐私信息"
  else
    echo "⚠️  发现隐私信息，详见报告: $REPORT_FILE"
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
    echo "  bash privacy-check.sh scan <文件路径>     # 扫描单个文件"
    echo "  bash privacy-check.sh scan-dir <目录路径> # 扫描整个目录"
    echo "  bash privacy-check.sh report              # 显示扫描报告"
    exit 1
    ;;
esac
