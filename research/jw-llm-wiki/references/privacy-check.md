# 隐私信息自查详解

> 版本: v3.0.0
> 更新: 2026-05-30

## 概述

隐私信息自查工具用于检测素材中的敏感信息，防止个人隐私、API 密钥等敏感数据被意外摄入到 wiki 中。

## 检测的隐私类型

### 个人身份信息 (PII)

| 类型 | 模式 | 示例 |
|------|------|------|
| 手机号 | `1[3-9][0-9]{9}` | 13812345678 |
| 身份证号 | `[1-9][0-9]{5}(19|20)[0-9]{2}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])[0-9]{3}[0-9Xx]` | 110101199001011234 |
| 邮箱地址 | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | user@example.com |
| 银行卡号 | `[0-9]{16,19}` | 6222021234567890123 |

### API 密钥和令牌

| 类型 | 模式 | 示例 |
|------|------|------|
| API 密钥 | `(sk\|ak\|key\|token\|secret\|password)[_-]?[=:\"' ]+[a-zA-Z0-9]{20,}` | sk-abc123... |
| SSH 私钥 | `-----BEGIN (RSA \|EC \|OPENSSH )?PRIVATE KEY-----` | -----BEGIN RSA PRIVATE KEY----- |
| JWT 令牌 | `eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*` | eyJhbGciOi... |
| AWS 密钥 | `AKIA[0-9A-Z]{16}` | AKIAIOSFODNN7EXAMPLE |
| GitHub Token | `gh[ps]_[A-Za-z0-9_]{36,}` | ghp_abc123... |
| OpenAI Key | `sk-[a-zA-Z0-9]{48,}` | sk-abc123... |

### 网络信息

| 类型 | 模式 | 示例 |
|------|------|------|
| IP 地址 | `([0-9]{1,3}\.){3}[0-9]{1,3}` | 192.168.1.1 |
| URL 参数 | `[?&](key\|token\|secret\|password\|api_key)=[^&]+` | ?api_key=abc123 |

## 使用方法

### 扫描单个文件

```bash
# 扫描单个文件
bash privacy-check.sh scan raw/articles/buffett-analysis.md

# 输出示例：
# === 隐私扫描 ===
# 文件: raw/articles/buffett-analysis.md
# 
# ⚠️  手机号: 2 处
#     示例: 138****5678
#     示例: 139****8765
# 
# ⚠️  邮箱地址: 1 处
#     示例: user****.com
# 
# ⚠️  发现 3 处潜在隐私信息
# 
# 建议：
# 1. 检查是否为真实个人信息
# 2. 如为示例数据，考虑脱敏后存储
# 3. 如为敏感信息，移除或加密存储
```

### 扫描整个目录

```bash
# 扫描整个目录
bash privacy-check.sh scan-dir raw/

# 输出示例：
# === 隐私扫描（目录） ===
# 目录: raw/
# 
# ⚠️  raw/articles/buffett-analysis.md (3 处)
# ⚠️  raw/articles/market-data.md (1 处)
# 
# === 扫描统计 ===
# 扫描文件数: 100
# 有问题文件: 2
# 问题总数: 4
# 
# ⚠️  发现隐私信息，详见报告: /root/wiki-ai/.privacy-scan-report.txt
```

### 显示扫描报告

```bash
# 显示扫描报告
bash privacy-check.sh report

# 输出示例：
# 隐私扫描报告 - 2026-05-30 10:00:00
# 目录: raw/
# ======================================
# 
# === raw/articles/buffett-analysis.md ===
# 手机号: 2 处
# 邮箱地址: 1 处
# 
# === raw/articles/market-data.md ===
# API密钥: 1 处
```

## 处理建议

### 1. 检查是否为真实个人信息

**场景：** 素材中包含真实的个人信息

**处理方法：**
- 如果是公开信息（如名人联系方式），可以保留
- 如果是私人信息，必须脱敏或删除

**示例：**
```markdown
# 脱敏前
联系方式：13812345678，邮箱：user@example.com

# 脱敏后
联系方式：138****5678，邮箱：user@example.com
```

### 2. 如为示例数据，考虑脱敏后存储

**场景：** 素材中的信息是示例或测试数据

**处理方法：**
- 使用脱敏工具处理
- 或手动替换为示例数据

**示例：**
```bash
# 使用 sed 脱敏
sed -i 's/1[3-9][0-9]\{9\}/138****5678/g' raw/articles/example.md
```

### 3. 如为敏感信息，移除或加密存储

**场景：** 素材中包含 API 密钥、私钥等敏感信息

**处理方法：**
- 立即移除敏感信息
- 如果需要保留，使用加密存储
- 通知相关人员更换密钥

**示例：**
```bash
# 移除 API 密钥
sed -i 's/sk-[a-zA-Z0-9]\{48,\}/sk-REDACTED/g' raw/articles/api-docs.md
```

## 最佳实践

### 1. 首次 ingest 前扫描

```bash
# 首次 ingest 前扫描
bash privacy-check.sh scan raw/articles/new-article.md

# 确认无隐私问题后再处理
# 如果有问题，先处理再 ingest
```

### 2. 批量处理前扫描

```bash
# 批量处理前扫描整个目录
bash privacy-check.sh scan-dir raw/articles/

# 根据扫描结果规划处理策略
# 如果有多个文件有问题，先批量处理
```

### 3. 定期扫描

```bash
# 每月扫描一次
bash privacy-check.sh scan-dir raw/

# 检查是否有新增的隐私信息
# 及时处理新发现的问题
```

### 4. 集成到工作流

```bash
# 在 ingest 工作流中集成隐私检查
# 1. 检查缓存
bash cache.sh check raw/articles/new-article.md

# 2. 检查隐私
bash privacy-check.sh scan raw/articles/new-article.md

# 3. 判断处理级别
bash content-grading.sh grade raw/articles/new-article.md

# 4. 处理素材
# ...
```

## 常见问题

### Q: 如何处理误报？

A: 如果扫描结果是误报：
1. 检查匹配的内容是否真的是隐私信息
2. 如果是误报，可以忽略
3. 如果需要，调整正则表达式减少误报

### Q: 如何添加新的隐私类型？

A: 编辑 `scripts/privacy-check.sh` 中的 PATTERNS 数组：
```bash
PATTERNS=(
  ["手机号"]="1[3-9][0-9]{9}"
  ["新类型"]="正则表达式"
)
```

### Q: 如何批量脱敏？

A: 使用 sed 或其他工具批量处理：
```bash
# 批量脱敏手机号
find raw/ -name "*.md" -exec sed -i 's/1[3-9][0-9]\{9\}/138****5678/g' {} \;

# 批量脱敏邮箱
find raw/ -name "*.md" -exec sed -i 's/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]\{2,\}/user@example.com/g' {} \;
```

### Q: 如何确保扫描全面？

A: 定期更新扫描规则：
1. 关注新的隐私信息类型
2. 更新正则表达式
3. 定期重新扫描已有素材

## 安全注意事项

1. **扫描报告包含敏感信息** - 报告文件 `.privacy-scan-report.txt` 可能包含匹配的敏感信息，需要妥善保管
2. **脱敏不可逆** - 脱敏后无法恢复原始信息，建议先备份
3. **密钥泄露需立即处理** - 如果发现 API 密钥泄露，立即更换密钥
4. **定期检查** - 定期扫描 wiki，确保没有新增的隐私信息
