---
domain: quanxue.cn
aliases: [劝学网]
updated: 2026-05-26
---

## 平台特征

- 静态HTML中文网站，章节/典籍内容分为**劝学网主站**（`/ct_rujia/`）和**诸子百家**（`/ct_baijia/`）两个子目录
- 页面编码：**UTF-8**（meta标签内声明），不要用gbk解码
- 内容结构：
  - 索引页：`<a href="xxxindex.html">` 列出一个典籍的所有章节页
  - 章节页：正文在 `<!-- 正文开始 -->` 到 `<!-- 正文结束 -->` 注释块内，或 `<div id="body">` 内
- 请求频率：0.3s/页 安全，建议不超过 1s/页

## URL 结构规律

```
# 主站（儒家典籍）
https://www.quanxue.cn/ct_rujia/{workid}index.html   # 索引页
https://www.quanxue.cn/ct_rujia/{workid}/{workid}NN.html  # 章节页

# 诸子百家（战国策等）
https://www.quanxue.cn/ct_baijia/{workid}index.html
https://www.quanxue.cn/ct_baijia/{workid}/{workid}NN.html
```

注意：法言(FaYan)首字母大写，实际路径为小写 `fayan/`。

## 有效抓取模式

1. 从索引页用正则 `href="([^"]*\.html)"` 提取所有章节路径
2. 过滤掉含 `index` 的路径和以 `http` 开头的外部链接
3. 编码处理（Python示例）：
   ```python
   raw = r.read()
   m = re.search(rb'charset=["\']?([^"\'\s]+)', raw[:2000])
   charset = m.group(1).decode('ascii', errors='ignore') if m else None
   html = raw.decode(charset) if charset else raw.decode('utf-8', errors='replace')
   ```
4. 正文提取优先顺序：`<!-- 正文开始 -->` → `<div id="body">` → `<p>` 文本块
5. 每页延迟 0.3s 以上

## 已知陷阱

- **GBK 误判**：错误地用 `decode("gbk")` 会导致中文乱码（显示为生僻字）。页面本身是 UTF-8，必须先用 meta charset 检测或默认 UTF-8 解码
- **大小写问题**：索引页里 `FaYan/FaYan01.html` 实际路径是 `fayan/fayan01.html`，抓取时需要修正
- **战国策在 ct_baijia**：不在 `ct_rujia` 下，索引页是 `/ct_baijia/zhanguoceindex.html`
- **周子全书/象山语要内容极少**：这两个典籍在劝学网上只有很少的章节，并非采集问题