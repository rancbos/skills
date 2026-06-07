#!/bin/bash
# jw-company-analysis 一致性检查脚本
# 用途：每次修改 SKILL.md 后自动执行，检查五端一致性
# 版本：v1.0.0

set -e

SKILL_DIR="${1:-$(dirname "$0")/..}"
SKILL_FILE="$SKILL_DIR/SKILL.md"
TEMPLATE_FILE="$SKILL_DIR/templates/company-analysis-report.md"
SCRIPT_FILE="$SKILL_DIR/scripts/pre_analysis.py"

echo "=========================================="
echo "jw-company-analysis 一致性检查"
echo "=========================================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

# 1. 版本号一致性检查
echo "📋 1. 版本号一致性检查"

SKILL_VERSION=$(grep -m1 'version:' "$SKILL_FILE" | grep -oP 'v?\d+\.\d+\.\d+' | head -1)
SKILL_TITLE_VERSION=$(grep -m1 '# 公司深度分析器' "$SKILL_FILE" | grep -oP 'v\d+\.\d+\.\d+' | head -1)
SCRIPT_VERSION=$(grep -oP 'v\d+\.\d+\.\d+' "$SCRIPT_FILE" 2>/dev/null | head -1 || echo "N/A")

echo "  SKILL.md frontmatter: $SKILL_VERSION"
echo "  SKILL.md 标题: $SKILL_TITLE_VERSION"
echo "  脚本版本: $SCRIPT_VERSION"

if [ "$SKILL_VERSION" != "$SKILL_TITLE_VERSION" ]; then
    echo -e "  ${RED}❌ 版本不一致：frontmatter($SKILL_VERSION) vs 标题($SKILL_TITLE_VERSION)${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "  ${GREEN}✅ frontmatter 与标题一致${NC}"
fi

# 2. 脚本路径一致性检查
echo ""
echo "📋 2. 脚本路径一致性检查"

if grep -q "rancbos-skills" "$SKILL_FILE"; then
    echo -e "  ${GREEN}✅ SKILL.md 使用 rancbos-skills 路径${NC}"
else
    echo -e "  ${RED}❌ SKILL.md 缺少 rancbos-skills 路径${NC}"
    ERRORS=$((ERRORS + 1))
fi

if grep -q "rancbos-skills" "$SCRIPT_FILE" 2>/dev/null; then
    echo -e "  ${GREEN}✅ 脚本使用 rancbos-skills 路径${NC}"
else
    echo -e "  ${YELLOW}⚠️ 脚本中未找到 rancbos-skills 路径（可能是动态构建）${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 3. references 文件健康检查
echo ""
echo "📋 3. references 文件健康检查"

MISSING_FILES=0
for ref in $(grep -oP 'references/[a-zA-Z0-9_-]+\.md' "$SKILL_FILE" | sort -u); do
    if [ ! -f "$SKILL_DIR/$ref" ]; then
        echo -e "  ${RED}❌ 引用的文件不存在：$ref${NC}"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ $MISSING_FILES -eq 0 ]; then
    echo -e "  ${GREEN}✅ 所有引用的文件都存在${NC}"
else
    ERRORS=$((ERRORS + MISSING_FILES))
fi

# 4. Step 3 标题一致性检查
echo ""
echo "📋 4. Step 3 标题一致性检查"

if grep -q '行业赛道与产业链' "$SKILL_FILE"; then
    echo -e "  ${RED}❌ SKILL.md 中仍有旧标题'行业赛道与产业链'${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo -e "  ${GREEN}✅ Step 3 标题已统一为'产业链与价值链'${NC}"
fi

# 5. 统计信息
echo ""
echo "=========================================="
echo "📊 检查结果汇总"
echo "=========================================="

TOTAL_FILES=$(ls "$SKILL_DIR"/references/*.md 2>/dev/null | wc -l)
echo "  references 文件数量: $TOTAL_FILES"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "  ${GREEN}✅ 全部通过！无错误无警告。${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "  ${YELLOW}⚠️ 有 $WARNINGS 个警告，无错误。${NC}"
    exit 0
else
    echo -e "  ${RED}❌ 有 $ERRORS 个错误，$WARNINGS 个警告。${NC}"
    exit 1
fi
