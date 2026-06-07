# 权威媒体网站 CDP 测试记录

测试日期：2026-05-29
测试环境：Chrome 148.0.7778.178 headless + CDP Proxy

## 测试结果

| 网站 | URL | 加载时间 | 新闻提取 | 备注 |
|------|-----|----------|---------|------|
| 新华网 | xinhuanet.com | ~4秒 | ✅ 成功 | 12条新闻标题+链接 |
| 人民网 | people.com.cn | ~6秒 | ✅ 成功 | 首次可能白屏，需重新导航 |
| 环球网 | huanqiu.com | ~6秒 | ✅ 成功 | 12条新闻标题+链接 |
| 百度搜索 | baidu.com/s?wd= | — | ❌ 失败 | 触发安全验证 |
| Bing 搜索 | bing.com/search?q= | ~3秒 | ✅ 成功 | 推荐替代百度 |

## 新闻标题提取 JS 模式

通用模式（适用于新华网、人民网、环球网）：

```javascript
JSON.stringify(
  Array.from(document.querySelectorAll("a[href]")).filter(a => {
    const text = a.textContent.trim();
    return text.length > 10 && text.length < 80 && !a.href.includes("javascript");
  }).slice(0, 12).map(a => ({
    title: a.textContent.trim().substring(0, 60),
    url: a.href
  }))
)
```

Bing 搜索结果提取：

```javascript
JSON.stringify(
  Array.from(document.querySelectorAll("#b_results .b_algo")).slice(0, 5).map(el => ({
    title: el.querySelector("h2 a")?.textContent || "",
    url: el.querySelector("h2 a")?.href || "",
    snippet: el.querySelector(".b_caption p")?.textContent || ""
  }))
)
```

## 操作要点

1. **首次 `/new` 可能白屏**：需要跟一次 `/navigate` + `sleep 3-5`
2. **人民网加载较慢**：需要 `sleep 6` 以上
3. **标题为空但 bodyLength > 0**：页面已加载但 JS 未完全执行，等待后重试
4. **百度安全验证无法绕过**：用 Bing 替代

## jw-news 集成建议

当搜索引擎 API 返回空时，可用 CDP 直访权威媒体网站作为降级方案：

```bash
# 创建页面
target=$(curl -s "http://localhost:3456/new?url=https://www.xinhuanet.com" \
  | grep -o '"targetId":"[^"]*"' | cut -d'"' -f4)
sleep 5

# 提取新闻
curl -s -X POST "http://localhost:3456/eval?target=$target" -d '...'
```
