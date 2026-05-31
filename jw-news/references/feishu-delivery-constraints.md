# 飞书消息发送限制（Feishu Delivery Constraints）

## 问题

在 cron/自动化环境中，通过 `lark-cli im +messages-send` 发送飞书消息会失败，原因是：

1. **Bot 身份**：Bot 不在任意群聊中（`Bot/User can NOT be out of the chat`），且无法主动拉人入群
2. **User 身份**：缺少 `im:message.send_as_user` scope，需完成 OAuth 交互式授权（`lark-cli auth login --scope "im:message.send_as_user"`），会输出 `verification_url` 阻塞等待浏览器授权，cron 环境无法完成此流程

## 结论

在纯 cron/headless 环境中，**无法通过 lark-cli 向飞书推送消息**。OAuth 授权流程必须在有浏览器交互的终端中完成。

## 解决方案

### 方案一：输出到 cron 投递（推荐）

在 cron 任务中，直接将格式化后的新闻早报作为最终输出返回。系统会自动将输出投递到配置的目的地（email/飞书通知等）。

```python
cronjob(
  action='create',
  name='每日新闻早报',
  schedule='50 7 * * *',
  skills=['jw-news'],
  prompt='...（内容不变）...',
  deliver='origin'  # 输出作为最终报告投递
)
```

### 方案二：手动完成 OAuth 后在 cron 中使用

1. 在交互式终端中完成：`lark-cli auth login --scope "im:message.send_as_user"`
2. 授权完成后，cron 任务中的 `lark-cli im +messages-send --as user` 将可以正常工作

### 方案三：使用飞书 Webhook 替代（需用户配置）

用户可配置飞书机器人的 Webhook，cron 任务通过 POST 请求发送消息，绕过 OAuth 限制。

## 判断逻辑

```
是否需要飞书推送？
  ├── 有交互式终端（用户在场）→ 先完成 OAuth，再用 lark-cli 发送
  ├── 无交互（cron/自动化）→ 将报告作为文本输出，依赖 cron投递机制
  └── 有 webhook 配置 → 通过 HTTP POST 发送
```

## 相关命令参考

```bash
# 检查 user identity 可用的聊天
lark-cli im +chat-list --as user --page-size 10

# 检查 bot identity 可用的聊天
lark-cli im +chat-list --as bot

# 测试发送（需 OAuth 完成）
lark-cli im +messages-send --as user --chat-id <chat_id> --text "测试"

# 查询消息发送所需 scope
lark-cli auth login --scope "im:message.send_as_user" --no-wait --json
```

## 已知限制

- cron 环境无法完成 `auth login` 的浏览器授权流程
- Bot 身份无法主动加入群聊（需要手动将 bot 拉入群）
- 即使完成了 OAuth，bot 也只能在它所在群中发消息