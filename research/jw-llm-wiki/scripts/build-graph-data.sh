#!/bin/bash
# build-graph-data.sh — 生成知识图谱数据 + 自动洞察
# 用法：bash build-graph-data.sh <wiki_root>
# 输出：graph-data.json（节点、边、洞察）
# 依赖：jq
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"


set -u

WIKI_ROOT="${1:-.}"
OUTPUT_FILE="$WIKI_ROOT/_meta/graph-data.json"

# 检查 jq 是否可用
if ! command -v jq >/dev/null 2>&1; then
  log_error "jq is not installed. Install via: apt install jq"
  exit 1
fi

# 确保目录存在
mkdir -p "$WIKI_ROOT/_meta"

echo "=== 生成知识图谱数据 ==="
echo "Wiki 路径: $WIKI_ROOT"
echo ""

# Step 1: 收集所有节点和边
echo "Step 1: 收集节点和边..."

# 临时文件
NODES_FILE=$(mktemp)
EDGES_FILE=$(mktemp)

# 收集所有 wikilinks
for subdir in entities concepts; do
  for f in "$WIKI_ROOT"/$subdir/*.md "$WIKI_ROOT"/$subdir/**/*.md; do
    [ -f "$f" ] || continue
    SOURCE=$(basename "$f" .md)
    
    # 提取 frontmatter 中的 category
    CATEGORY=$(grep "^category:" "$f" 2>/dev/null | head -1 | sed 's/category: *//')
    [ -z "$CATEGORY" ] && CATEGORY="unknown"
    
    # 提取 frontmatter 中的 type
    TYPE=$(grep "^type:" "$f" 2>/dev/null | head -1 | sed 's/type: *//')
    [ -z "$TYPE" ] && TYPE="unknown"
    
    # 记录节点
    echo "$SOURCE|$CATEGORY|$TYPE" >> "$NODES_FILE"
    
    # 提取 wikilinks
    grep -oP '\[\[[^\]]+\]\]' "$f" 2>/dev/null |       sed 's/\[\[//;s/\]\]//' |       sed 's/|.*//' |       while read -r TARGET; do
        [ -z "$TARGET" ] && continue
        # 只记录有效的边（目标文件存在）
        for check_dir in entities concepts; do
          if [ -f "$WIKI_ROOT/$check_dir/$TARGET.md" ]; then
            echo "$SOURCE|$TARGET" >> "$EDGES_FILE"
            break
          fi
        done
      done
  done
done

# 去重节点
sort -u "$NODES_FILE" > "$NODES_FILE.tmp"
mv "$NODES_FILE.tmp" "$NODES_FILE"

# 去重边
sort -u "$EDGES_FILE" > "$EDGES_FILE.tmp"
mv "$EDGES_FILE.tmp" "$EDGES_FILE"

NODE_COUNT=$(wc -l < "$NODES_FILE")
EDGE_COUNT=$(wc -l < "$EDGES_FILE")

echo "  节点数: $NODE_COUNT"
echo "  边数: $EDGE_COUNT"
echo ""

# Step 2: 计算度数
echo "Step 2: 计算度数..."

DEGREE_FILE=$(mktemp)
while IFS='|' read -r NODE CATEGORY TYPE; do
  # 计算入度（被引用次数）
  IN_DEG=$(grep -c "|$NODE$" "$EDGES_FILE" 2>/dev/null || true)
  IN_DEG=${IN_DEG:-0}
  # 计算出度（引用其他页面次数）
  OUT_DEG=$(grep -c "^$NODE|" "$EDGES_FILE" 2>/dev/null || true)
  OUT_DEG=${OUT_DEG:-0}
  # 总度数
  TOTAL_DEG=$((IN_DEG + OUT_DEG))
  echo "$NODE $CATEGORY $TYPE $IN_DEG $OUT_DEG $TOTAL_DEG" >> "$DEGREE_FILE"
done < "$NODES_FILE"

echo "  完成"
echo ""

# Step 3: 生成洞察
echo "Step 3: 生成洞察..."

INSIGHTS_FILE=$(mktemp)

# 3.1 高度数节点（核心概念）
echo "  查找核心概念..."
sort -k6 -rn "$DEGREE_FILE" | head -10 | while read -r NODE CATEGORY TYPE IN_DEG OUT_DEG TOTAL_DEG; do
  echo "核心概念: $NODE (总度数: $TOTAL_DEG, 入度: $IN_DEG, 出度: $OUT_DEG, 分类: $CATEGORY)" >> "$INSIGHTS_FILE"
done

# 3.2 知识缺口（低度数节点）
echo "  查找知识缺口..."
sort -k6 -n "$DEGREE_FILE" | head -10 | while read -r NODE CATEGORY TYPE IN_DEG OUT_DEG TOTAL_DEG; do
  if [ "$TOTAL_DEG" -le 2 ]; then
    echo "知识缺口: $NODE (总度数: $TOTAL_DEG, 分类: $CATEGORY)" >> "$INSIGHTS_FILE"
  fi
done

# 3.3 孤立节点（无入链）
echo "  查找孤立节点..."
ORPHAN_COUNT=0
while read -r NODE CATEGORY TYPE IN_DEG OUT_DEG TOTAL_DEG; do
  if [ "$IN_DEG" -eq 0 ]; then
    ORPHAN_COUNT=$((ORPHAN_COUNT + 1))
  fi
done < "$DEGREE_FILE"
echo "孤立节点（无入链）: $ORPHAN_COUNT" >> "$INSIGHTS_FILE"

# 3.4 分类统计
echo "  统计分类分布..."
awk '{print $2}' "$DEGREE_FILE" | sort | uniq -c | sort -rn | head -10 | while read -r COUNT CATEGORY; do
  echo "分类: $CATEGORY ($COUNT 个节点)" >> "$INSIGHTS_FILE"
done

echo "  完成"
echo ""

# Step 4: 生成 JSON 输出
echo "Step 4: 生成 JSON..."

# 构建节点 JSON
NODES_JSON=$(while read -r NODE CATEGORY TYPE IN_DEG OUT_DEG TOTAL_DEG; do
  echo "{\"id\":\"$NODE\",\"category\":\"$CATEGORY\",\"type\":\"$TYPE\",\"in_degree\":$IN_DEG,\"out_degree\":$OUT_DEG,\"total_degree\":$TOTAL_DEG}"
done < "$DEGREE_FILE" | jq -s '.')

# 构建边 JSON
EDGES_JSON=$(while IFS='|' read -r SOURCE TARGET; do
  echo "{\"source\":\"$SOURCE\",\"target\":\"$TARGET\"}"
done < "$EDGES_FILE" | jq -s '.')

# 构建洞察 JSON
INSIGHTS_JSON=$(cat "$INSIGHTS_FILE" 2>/dev/null | jq -R -s 'split("\n") | map(select(length > 0))')

# 构建统计 JSON
STATS_JSON=$(jq -n \
  --argjson node_count "$NODE_COUNT" \
  --argjson edge_count "$EDGE_COUNT" \
  --argjson orphan_count "$ORPHAN_COUNT" \
  '{
    "node_count": $node_count,
    "edge_count": $edge_count,
    "orphan_count": $orphan_count
  }')

# 组装最终 JSON
jq -n \
  --argjson nodes "$NODES_JSON" \
  --argjson edges "$EDGES_JSON" \
  --argjson insights "$INSIGHTS_JSON" \
  --argjson stats "$STATS_JSON" \
  '{
    "generated_at": (now | strftime("%Y-%m-%d %H:%M:%S")),
    "stats": $stats,
    "nodes": $nodes,
    "edges": $edges,
    "insights": $insights
  }' > "$OUTPUT_FILE"

echo "  输出文件: $OUTPUT_FILE"
echo ""

# 清理临时文件
rm -f "$NODES_FILE" "$EDGES_FILE" "$DEGREE_FILE" "$INSIGHTS_FILE"

# 输出统计
echo "=== 完成 ==="
echo "节点数: $NODE_COUNT"
echo "边数: $EDGE_COUNT"
echo "孤立节点: $ORPHAN_COUNT"
echo ""

# 输出洞察
echo "=== 洞察 ==="
if [ -s "$OUTPUT_FILE" ]; then
  jq -r '.insights[]' "$OUTPUT_FILE" 2>/dev/null | head -20
fi

exit 0
