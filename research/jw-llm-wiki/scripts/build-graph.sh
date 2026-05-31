#!/bin/bash
# build-graph.sh — 知识图谱可视化
# 用法：
#   bash build-graph.sh mermaid           # 生成 Mermaid 图
#   bash build-graph.sh html              # 生成交互式 HTML
#   bash build-graph.sh stats             # 显示图谱统计
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

GRAPH_DIR="$WIKI_ROOT/_meta"
MERMAID_FILE="$GRAPH_DIR/knowledge-graph.mmd"
HTML_FILE="$GRAPH_DIR/knowledge-graph.html"

# 确保目录存在
mkdir -p "$GRAPH_DIR"

# 提取 wikilinks
extract_links() {
  local dir="$1"
  local output_file="$2"
  
  > "$output_file"
  
  # 遍历所有 md 文件
  while IFS= read -r -d '' file; do
    local source
    source=$(basename "$file" .md)
    
    # 提取 wikilinks
    grep -oP '\[\[([^\]]+)\]\]' "$file" 2>/dev/null | while read -r link; do
      # 清理链接
      local target
      target=$(echo "$link" | sed 's/\[\[//;s/\]\]//' | sed 's/|.*//')  # 处理 piped links
      echo "$source -> $target" >> "$output_file"
    done
  done < <(find "$dir" -name "*.md" -type f -print0)
}

# 生成 Mermaid 图
generate_mermaid() {
  echo "=== 生成 Mermaid 图 ==="
  
  local links_file="$GRAPH_DIR/.links-temp.txt"
  extract_links "$WIKI_ROOT/entities" "$links_file"
  extract_links "$WIKI_ROOT/concepts" "$links_file"
  
  # 开始写 Mermaid 文件
  cat > "$MERMAID_FILE" << 'EOF'
graph TD
  %% 节点样式定义
  classDef rujia fill:#e1f5fe,stroke:#0288d1,stroke-width:2px
  classDef dao fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
  classDef fajia fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
  classDef baojia fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
  classDef bingjia fill:#fce4ec,stroke:#c62828,stroke-width:2px
  classDef invest fill:#f1f8e9,stroke:#558b2f,stroke-width:2px
  classDef malie fill:#ede7f6,stroke:#4527a0,stroke-width:2px
  classDef concept fill:#fff9c4,stroke:#f9a825,stroke-width:2px
  classDef default fill:#f5f5f5,stroke:#616161,stroke-width:1px

EOF
  
  # 添加节点和边
  while IFS= read -r line; do
    local source target
    source=$(echo "$line" | awk -F' -> ' '{print $1}')
    target=$(echo "$line" | awk -F' -> ' '{print $2}')
    
    # 确定节点样式
    local source_class="default"
    local target_class="default"
    
    # 检查文件所在目录确定分类
    for dir in rujia dao fajia baojia bingjia invest malie; do
      if [ -d "$WIKI_ROOT/entities/$dir" ]; then
        if find "$WIKI_ROOT/entities/$dir" -name "${source}.md" -print -quit 2>/dev/null | grep -q .; then
          source_class="$dir"
        fi
        if find "$WIKI_ROOT/entities/$dir" -name "${target}.md" -print -quit 2>/dev/null | grep -q .; then
          target_class="$dir"
        fi
      fi
    done
    
    # 检查是否是 concept
    if [ -d "$WIKI_ROOT/concepts" ]; then
      if find "$WIKI_ROOT/concepts" -name "${source}.md" -print -quit 2>/dev/null | grep -q .; then
        source_class="concept"
      fi
      if find "$WIKI_ROOT/concepts" -name "${target}.md" -print -quit 2>/dev/null | grep -q .; then
        target_class="concept"
      fi
    fi
    
    # 输出 Mermaid 语法
    echo "  $source[$source] --> $target[$target]" >> "$MERMAID_FILE"
    echo "  class $source $source_class" >> "$MERMAID_FILE"
    echo "  class $target $target_class" >> "$MERMAID_FILE"
  done < "$links_file"
  
  # 清理临时文件
  rm -f "$links_file"
  
  echo "Mermaid 图已生成: $MERMAID_FILE"
  echo ""
  echo "使用方法："
  echo "1. 在 Obsidian 中直接渲染（安装 Mermaid 插件）"
  echo "2. 在线渲染: https://mermaid.live/"
  echo "3. 转换为图片: mmdc -i $MERMAID_FILE -o graph.png"
}

# 生成交互式 HTML
generate_html() {
  echo "=== 生成交互式 HTML ==="
  
  local links_file="$GRAPH_DIR/.links-temp.txt"
  extract_links "$WIKI_ROOT/entities" "$links_file"
  extract_links "$WIKI_ROOT/concepts" "$links_file"
  
  # 收集所有节点和边
  local nodes=""
  local edges=""
  local node_set=""
  
  while IFS= read -r line; do
    local source target
    source=$(echo "$line" | awk -F' -> ' '{print $1}')
    target=$(echo "$line" | awk -F' -> ' '{print $2}')
    
    # 添加节点（去重）
    if ! echo "$node_set" | grep -q "^$source$"; then
      nodes="$nodes { id: '$source', label: '$source', group: 'entity' },"
      node_set="$node_set\n$source"
    fi
    if ! echo "$node_set" | grep -q "^$target$"; then
      nodes="$nodes { id: '$target', label: '$target', group: 'entity' },"
      node_set="$node_set\n$target"
    fi
    
    # 添加边
    edges="$edges { from: '$source', to: '$target' },"
  done < "$links_file"
  
  # 清理临时文件
  rm -f "$links_file"
  
  # 生成 HTML
  cat > "$HTML_FILE" << EOF
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Wiki 知识图谱</title>
  <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
    #graph { width: 100%; height: 100vh; }
    .controls { position: fixed; top: 10px; left: 10px; z-index: 1000; }
    .controls button { margin: 5px; padding: 8px 12px; cursor: pointer; }
    .legend { position: fixed; bottom: 10px; right: 10px; background: white; padding: 10px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }
    .legend div { margin: 5px 0; }
    .legend span { display: inline-block; width: 12px; height: 12px; margin-right: 5px; vertical-align: middle; }
  </style>
</head>
<body>
  <div class="controls">
    <button onclick="network.fit()">适应窗口</button>
    <button onclick="network.zoomIn()">放大</button>
    <button onclick="network.zoomOut()">缩小</button>
    <input type="text" id="search" placeholder="搜索节点..." oninput="searchNode(this.value)">
  </div>
  <div id="graph"></div>
  <div class="legend">
    <div><span style="background:#e1f5fe"></span>儒家</div>
    <div><span style="background:#f3e5f5"></span>道家</div>
    <div><span style="background:#fff3e0"></span>法家</div>
    <div><span style="background:#e8f5e9"></span>诸子百家</div>
    <div><span style="background:#fce4ec"></span>兵家</div>
    <div><span style="background:#f1f8e9"></span>投资</div>
    <div><span style="background:#ede7f6"></span>马列</div>
    <div><span style="background:#fff9c4"></span>概念</div>
  </div>
  <script>
    const nodes = new vis.DataSet([${nodes}]);
    const edges = new vis.DataSet([${edges}]);
    
    const container = document.getElementById('graph');
    const data = { nodes, edges };
    const options = {
      nodes: {
        shape: 'dot',
        size: 10,
        font: { size: 12, face: 'Arial' },
        borderWidth: 2,
        shadow: true
      },
      edges: {
        width: 1,
        color: { color: '#848484', highlight: '#848484' },
        arrows: { to: { enabled: true, scaleFactor: 0.5 } },
        smooth: { type: 'continuous' }
      },
      physics: {
        barnesHut: {
          gravitationalConstant: -2000,
          springLength: 150
        },
        stabilization: { iterations: 250 }
      },
      interaction: {
        hover: true,
        tooltipDelay: 200
      }
    };
    
    const network = new vis.Network(container, data, options);
    
    function searchNode(query) {
      if (!query) {
        nodes.forEach(node => {
          nodes.update({ id: node.id, opacity: 1 });
        });
        return;
      }
      
      query = query.toLowerCase();
      nodes.forEach(node => {
        const match = node.label.toLowerCase().includes(query);
        nodes.update({ id: node.id, opacity: match ? 1 : 0.2 });
      });
    }
    
    network.on('click', function(params) {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const node = nodes.get(nodeId);
        alert('节点: ' + node.label + '\\n链接数: ' + network.getConnectedNodes(nodeId).length);
      }
    });
  </script>
</body>
</html>
EOF
  
  echo "交互式 HTML 已生成: $HTML_FILE"
  echo ""
  echo "使用方法："
  echo "1. 在浏览器中打开: file://$HTML_FILE"
  echo "2. 部署到 Web 服务器供团队访问"
}

# 显示图谱统计
show_stats() {
  echo "=== 知识图谱统计 ==="
  echo ""
  
  # 统计节点数
  local entity_count
  entity_count=$(find "$WIKI_ROOT/entities" -name "*.md" -type f | wc -l)
  local concept_count
  concept_count=$(find "$WIKI_ROOT/concepts" -name "*.md" -type f | wc -l)
  local total_nodes=$((entity_count + concept_count))
  
  echo "节点数: $total_nodes"
  echo "  实体: $entity_count"
  echo "  概念: $concept_count"
  echo ""
  
  # 统计边数（wikilinks）
  local total_links=0
  while IFS= read -r -d '' file; do
    local links
    links=$(grep -cP '\[\[([^\]]+)\]\]' "$file" 2>/dev/null || echo "0")
    total_links=$((total_links + links))
  done < <(find "$WIKI_ROOT/entities" "$WIKI_ROOT/concepts" -name "*.md" -type f -print0)
  
  echo "边数（wikilinks）: $total_links"
  echo "平均链接数: $((total_links / total_nodes))"
  echo ""
  
  # 统计各分类节点数
  echo "分类分布:"
  for dir in rujia dao fajia baojia bingjia invest malie; do
    if [ -d "$WIKI_ROOT/entities/$dir" ]; then
      local count
      count=$(find "$WIKI_ROOT/entities/$dir" -name "*.md" -type f | wc -l)
      echo "  $dir: $count"
    fi
  done
  
  echo ""
  echo "孤立节点（无入链）:"
  # 这个统计需要更复杂的逻辑，这里简化处理
  echo "  （需要运行 lint 获取详细数据）"
}

# 主入口
case "${1:-}" in
  mermaid)
    generate_mermaid
    ;;
  html)
    generate_html
    ;;
  stats)
    show_stats
    ;;
  *)
    echo "用法："
    echo "  bash build-graph.sh mermaid    # 生成 Mermaid 图"
    echo "  bash build-graph.sh html       # 生成交互式 HTML"
    echo "  bash build-graph.sh stats      # 显示图谱统计"
    exit 1
    ;;
esac
