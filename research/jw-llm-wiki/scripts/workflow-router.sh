#!/bin/bash
# workflow-router.sh — 工作流路由器（真正工作的版本）
# 统一入口，根据用户意图路由到对应的工作流
# 用法: bash workflow-router.sh <action> [args...]

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# 检测 Wiki 根目录
detect_wiki_root() {
  local override="${1:-}"
  if [ -n "$override" ] && [ -d "$override" ]; then echo "$override"; return 0; fi
  if [ -n "${WIKI_PATH:-}" ] && [ -d "$WIKI_PATH" ]; then echo "$WIKI_PATH"; return 0; fi
  if [ -f "$HOME/.llm-wiki-path" ]; then
    local p; p=$(cat "$HOME/.llm-wiki-path" 2>/dev/null)
    [ -n "$p" ] && [ -d "$p" ] && echo "$p" && return 0
  fi
  [ -f "./SCHEMA.md" ] && echo "$(pwd)" && return 0
  return 1
}

ACTION="${1:-help}"
WIKI_ROOT=$(detect_wiki_root "${2:-}")
shift 2>/dev/null || true

case "$ACTION" in
  ingest)
    SOURCE="${1:-}"
    if [ -z "$SOURCE" ]; then
      log_error "缺少素材来源"
      echo "用法: workflow-router.sh ingest <URL|文件路径>"
      exit 1
    fi
    if [ -z "$WIKI_ROOT" ]; then
      log_error "未找到知识库，请设置 WIKI_PATH"
      exit 1
    fi
    
    log_info "=== Ingest 管线启动 ==="
    log_info "素材: $SOURCE"
    log_info "Wiki: $WIKI_ROOT"
    echo ""
    
    # Step 1: 缓存检查
    log_info "Step 1/5: 缓存检查..."
    if [ -f "$SOURCE" ]; then
      CACHE_RESULT=$(bash "$SCRIPT_DIR/cache.sh" check "$SOURCE" 2>/dev/null || echo "MISS:error")
      echo "  缓存结果: $CACHE_RESULT"
      if [[ "$CACHE_RESULT" == HIT* ]]; then
        log_ok "缓存命中，跳过处理"
        exit 0
      fi
    else
      log_warn "非本地文件，跳过缓存检查"
    fi
    
    # Step 2: 内容分级
    log_info "Step 2/5: 内容分级..."
    if [ -f "$SOURCE" ]; then
      bash "$SCRIPT_DIR/content-grading.sh" grade "$SOURCE" 2>/dev/null || true
    fi
    echo ""
    
    # Step 3: 隐私检查
    log_warn "Step 3/5: 请确认素材中不包含敏感信息（手机号、身份证、API密钥等）"
    echo ""
    
    # Step 4: 两步处理流程提示
    log_info "Step 4/5: 请 Agent 执行两步处理流程："
    echo "  1. Step 1: 结构化分析 → 输出 JSON"
    echo "  2. 验证 JSON: bash $SCRIPT_DIR/validate-step1.sh /tmp/step1.json"
    echo "  3. Step 2: 基于 JSON 生成 wiki 页面"
    echo ""
    
    # Step 5: 完成后更新缓存
    log_info "Step 5/5: 处理完成后更新缓存:"
    echo "  bash $SCRIPT_DIR/cache.sh update '$SOURCE'"
    echo ""
    
    log_ok "Ingest 管线准备就绪，请 Agent 执行后续步骤"
    ;;
    
  query)
    QUESTION="${1:-}"
    if [ -z "$QUESTION" ]; then
      log_error "缺少查询问题"
      exit 1
    fi
    if [ -z "$WIKI_ROOT" ]; then
      log_error "未找到知识库"
      exit 1
    fi
    
    log_info "查询: $QUESTION"
    echo ""
    
    # 别名展开
    ALIASES_FILE="$WIKI_ROOT/.wiki-aliases.json"
    if [ -f "$ALIASES_FILE" ]; then
      log_info "别名展开..."
      bash "$SCRIPT_DIR/alias-manager.sh" expand "$QUESTION" 2>/dev/null || true
    fi
    
    # 搜索
    log_info "搜索相关页面..."
    echo "  请 Agent 执行: search_files \"$QUESTION\" path=\"$WIKI_ROOT\" file_glob=\"*.md\""
    ;;
    
  digest)
    TOPIC="${1:-}"
    FORMAT="${2:-deep}"
    if [ -z "$TOPIC" ]; then
      log_error "缺少主题"
      exit 1
    fi
    if [ -z "$WIKI_ROOT" ]; then
      log_error "未找到知识库"
      exit 1
    fi
    
    log_info "Digest: $TOPIC (格式: $FORMAT)"
    bash "$SCRIPT_DIR/digest.sh" search "$TOPIC" "$WIKI_ROOT"
    ;;
    
  lint)
    FIX_MODE=false
    [ "${1:-}" = "--fix" ] && FIX_MODE=true
    if [ -z "$WIKI_ROOT" ]; then
      log_error "未找到知识库"
      exit 1
    fi
    
    log_info "=== 健康检查 ==="
    echo ""
    
    # 机械检查
    log_info "Step 1: 机械检查..."
    bash "$SCRIPT_DIR/lint-runner.sh" "$WIKI_ROOT"
    LINT_EXIT=$?
    
    if [ $LINT_EXIT -ne 0 ]; then
      log_error "lint-runner.sh 执行失败"
      exit 1
    fi
    echo ""
    
    # 自动修复
    if [ "$FIX_MODE" = true ]; then
      log_info "Step 2: 自动修复..."
      bash "$SCRIPT_DIR/lint-fix.sh" "$WIKI_ROOT"
    fi
    
    # 来源覆盖
    log_info "Step 3: 来源覆盖检查..."
    bash "$SCRIPT_DIR/source-signal-coverage.sh" "$WIKI_ROOT" 2>/dev/null | grep -E "来源覆盖率|缺少|为空" || true
    ;;
    
  status)
    if [ -z "$WIKI_ROOT" ]; then
      log_error "未找到知识库"
      exit 1
    fi
    
    log_info "=== 知识库状态 ==="
    echo "路径: $WIKI_ROOT"
    echo ""
    
    # 页面统计
    ENTITY_COUNT=$(find "$WIKI_ROOT/entities" -name "*.md" -type f 2>/dev/null | wc -l)
    CONCEPT_COUNT=$(find "$WIKI_ROOT/concepts" -name "*.md" -type f 2>/dev/null | wc -l)
    TOTAL=$((ENTITY_COUNT + CONCEPT_COUNT))
    
    echo "页面统计:"
    echo "  实体: $ENTITY_COUNT"
    echo "  概念: $CONCEPT_COUNT"
    echo "  总计: $TOTAL"
    echo ""
    
    # 来源覆盖
    bash "$SCRIPT_DIR/source-signal-coverage.sh" "$WIKI_ROOT" 2>/dev/null | grep "来源覆盖率" || echo "  来源覆盖: 未知"
    echo ""
    
    # 最近活动
    if [ -f "$WIKI_ROOT/log.md" ]; then
      echo "最近活动:"
      tail -5 "$WIKI_ROOT/log.md" 2>/dev/null | sed 's/^/  /'
    fi
    ;;
    
  graph)
    if [ -z "$WIKI_ROOT" ]; then
      log_error "未找到知识库"
      exit 1
    fi
    
    log_info "生成知识图谱..."
    bash "$SCRIPT_DIR/build-graph-data.sh" "$WIKI_ROOT"
    ;;
    
  delete)
    FILE="${1:-}"
    if [ -z "$FILE" ]; then
      log_error "缺少文件路径"
      exit 1
    fi
    
    log_info "删除: $FILE"
    bash "$SCRIPT_DIR/delete-helper.sh" scan "$FILE"
    ;;
    
  crystallize)
    CONTENT="${1:-}"
    SOURCE="${2:-对话}"
    if [ -z "$CONTENT" ]; then
      log_error "缺少洞见内容"
      exit 1
    fi
    
    log_info "结晶化: ${CONTENT:0:30}..."
    bash "$SCRIPT_DIR/crystallize.sh" save "$CONTENT" "$SOURCE"
    ;;
    
  crosslink)
    if [ -z "$WIKI_ROOT" ]; then
      log_error "未找到知识库"
      exit 1
    fi
    
    log_info "自动跨链..."
    bash "$SCRIPT_DIR/crosslink.sh" "$WIKI_ROOT" "$@"
    ;;
    
  fix)
    if [ -z "$WIKI_ROOT" ]; then
      log_error "未找到知识库"
      exit 1
    fi
    
    log_info "自动修复..."
    bash "$SCRIPT_DIR/lint-fix.sh" "$WIKI_ROOT"
    ;;
    
  privacy)
    TARGET="${1:-}"
    if [ -z "$TARGET" ]; then
      log_error "缺少扫描目标"
      exit 1
    fi
    
    log_info "隐私检查: $TARGET"
    if [ -d "$TARGET" ]; then
      bash "$SCRIPT_DIR/privacy-check.sh" scan-dir "$TARGET"
    else
      bash "$SCRIPT_DIR/privacy-check.sh" scan "$TARGET"
    fi
    ;;
    
  images)
    TARGET="${1:-}"
    if [ -z "$TARGET" ]; then
      log_error "缺少扫描目标"
      exit 1
    fi
    
    log_info "图片追踪: $TARGET"
    if [ -d "$TARGET" ]; then
      bash "$SCRIPT_DIR/image-tracker.sh" scan-dir "$TARGET"
    else
      bash "$SCRIPT_DIR/image-tracker.sh" scan "$TARGET"
    fi
    ;;
    
  help|*)
    echo "用法: workflow-router.sh <action> [args...]"
    echo ""
    echo "核心工作流:"
    echo "  ingest <source>        摄入素材（URL/文件）"
    echo "  query <question>       查询知识库"
    echo "  digest <topic> [fmt]   深度综合报告"
    echo "  lint [--fix]           健康检查"
    echo "  status                 查看状态"
    echo ""
    echo "辅助工具:"
    echo "  graph                  知识图谱"
    echo "  delete <file>          安全删除"
    echo "  crystallize <content>  结晶化洞见"
    echo "  crosslink [--full]     自动跨链"
    echo "  fix                    自动修复"
    echo "  privacy <target>       隐私检查"
    echo "  images <target>        图片追踪"
    ;;
esac
