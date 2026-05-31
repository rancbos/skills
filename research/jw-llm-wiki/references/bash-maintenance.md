# Bash 脚本维护陷阱

> 从 jw-llm-wiki 多轮脚本编辑中提炼的经验。

## 1. grep -c 返回 "0\n0" 问题

**问题：**
```bash
count=$(grep -c "pattern" file 2>/dev/null || echo "0")
# 当 grep 无匹配时，退出码为 1，|| echo "0" 也会执行
# 结果是 "0\n0"（两个 0 用换行分隔）
```

**正确写法：**
```bash
count=$(grep -c "pattern" file 2>/dev/null || true)
count=${count:-0}
```

或使用 common.sh 的 `safe_grep_count`：
```bash
count=$(safe_grep_count "pattern" file)
```

## 2. Bash 关联数组 + set -u 报 unbound variable

**问题：**
```bash
set -u
declare -A MY_ARRAY
echo "${MY_ARRAY[nonexistent_key]}"  # 报错：unbound variable
```

**解决方案：**
```bash
# 方案 1：用临时文件 + grep 代替关联数组
echo "key1 value1" > /tmp/lookup.txt
value=$(grep "^$key " /tmp/lookup.txt | awk '{print $2}')

# 方案 2：用 set +u 临时关闭
set +u
value="${MY_ARRAY[$key]}"
set -u

# 方案 3：用默认值
value="${MY_ARRAY[$key]:-default}"
```

## 3. Regex 替换破坏 bash 语法

**问题：**
用 regex 批量替换 bash 脚本时，容易破坏括号和引号：
```bash
# 试图替换 echo "ERROR:" 为 log_error("
# 但 echo "ERROR: message" >&2 被替换为 log_error(" message") >&2
# 语法错误：多余的右括号
```

**正确做法：**
1. 替换后必须用 `bash -n <file>` 验证语法
2. 用更精确的 regex，避免匹配错误的上下文
3. 考虑用 sed 而不是 Python regex（更可控）

**验证脚本：**
```bash
for f in scripts/*.sh; do
  if ! bash -n "$f" 2>/dev/null; then
    echo "❌ $f: 语法错误"
  else
    echo "✅ $f"
  fi
done
```

## 4. common.sh source 但不使用

**问题：**
```bash
source "$SCRIPT_DIR/lib/common.sh"
# 但仍然自己写 WIKI_ROOT 检测逻辑
if [ -n "${WIKI_PATH:-}" ]; then
  WIKI_ROOT="$WIKI_PATH"
elif ...
```

**正确做法：**
```bash
source "$SCRIPT_DIR/lib/common.sh"
# 使用 common.sh 的函数
WIKI_ROOT=$(detect_wiki_root "${1:-}")
if [ -z "$WIKI_ROOT" ]; then
  log_error "未找到知识库"
  exit 1
fi
```

## 5. workflow-router.sh 只打印不执行

**问题：**
```bash
# 只打印提示，不实际调用脚本
echo "请 Agent 执行: bash $SCRIPT_DIR/xxx.sh"
```

**正确做法：**
```bash
# 实际调用脚本
bash "$SCRIPT_DIR/xxx.sh" "$WIKI_ROOT"
```

## 6. jq --argjson 需要有效 JSON

**问题：**
```bash
jq -n --argjson var "$value"  # 如果 $value 不是有效 JSON 会报错
```

**正确做法：**
```bash
# 用 --arg 传字符串，在 jq 内转换
jq -n --arg var "$value" '.field = $var'

# 或先验证 JSON
echo "$value" | jq empty 2>/dev/null || { echo "Invalid JSON"; exit 1; }
```

## 7. 批量编辑脚本的安全流程

1. **备份原文件**：`cp file file.bak`
2. **用精确的 regex**：避免误匹配
3. **验证语法**：`bash -n file`
4. **功能测试**：运行脚本检查输出
5. **回滚机制**：如果出错，恢复备份

## 8. read_file 返回值含行号前缀

**问题：**
read_file 输出格式为 `     1|内容`，直接 write_file 回去会把行号写入文件。

**正确做法：**
```python
# 用 Python 直接读写
with open(filepath, 'r') as f:
    content = f.read()

# 处理内容
# ...

with open(filepath, 'w') as f:
    f.write(content)
```

或用 sed 剥离行号：
```bash
sed -i 's/^[[:space:]]*[0-9]*|//' file
```
