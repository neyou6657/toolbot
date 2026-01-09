# Telegram BIN Info Bot - 部署指南

## 📋 部署到 HuggingFace Spaces

### 第一步：准备工作

1. **创建 Telegram Bot**
   - 在 Telegram 中找到 [@BotFather](https://t.me/BotFather)
   - 发送 `/newbot` 创建新机器人
   - 保存返回的 Bot Token（格式如：`123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`）

2. **配置 Cloudflare Worker**
   - 该项目已包含 `cf2tgapi.js` 文件
   - 在 Cloudflare Workers 中创建新 Worker
   - 复制 `cf2tgapi.js` 的内容到 Worker
   - 绑定你的域名（例如 `你的域名.workers.dev` 或自定义域名）

### 第二步：创建 HuggingFace Space

1. 访问 [HuggingFace Spaces](https://huggingface.co/spaces)
2. 点击 "Create new Space"
3. 配置如下：
   - **Owner**: 你的用户名
   - **Space name**: 例如 `telegram-bin-bot`
   - **License**: MIT
   - **Select the Space SDK**: Docker
   - **Space hardware**: CPU basic (免费)
   - **Visibility**: Private（私有空间）

### 第三步：上传代码

将以下文件上传到你的 Space 仓库：

```
├── Dockerfile
├── requirements.txt
├── bot.py
├── get_bininfo.py
├── README.md
└── .gitignore (可选)
```

**方式 A：通过 Git**
```bash
git clone https://huggingface.co/spaces/你的用户名/你的空间名
cd 你的空间名
cp /home/zywoo/huggingface/tgbot/* .
git add .
git commit -m "Initial commit"
git push
```

**方式 B：通过网页界面**
直接在 HuggingFace 网页上传文件

### 第四步：配置环境变量（Secrets）

在你的 Space 设置中添加以下 Secrets：

1. 进入 Space 的 "Settings" 标签
2. 找到 "Repository secrets" 部分
3. 添加以下 Secret：

| Name | Value |
|------|-------|
| `TELEGRAM_BOT_TOKEN` | 你的 Bot Token（从 BotFather 获取）|
| `TELEGRAM_API_BASE` | 你的 Cloudflare Worker 反代 URL（如 `https://你的域名/telegram-api`）|

**注意**：`POLLING_INTERVAL` 可选，默认为 10 秒。

### 第五步：等待部署

1. 保存后，HuggingFace 会自动构建 Docker 镜像
2. 构建过程大约需要 2-5 分钟
3. 在 "Build" 标签中可以查看构建日志
4. 构建成功后，机器人会自动启动

### 第六步：验证运行

1. 在 "Logs" 标签中查看运行日志
2. 应该能看到类似以下的日志：
   ```
   Health check server started on port 7860
   Bot connected: @你的机器人用户名
   Bot starting...
   ```
3. 在 Telegram 中向你的机器人发送 `/start` 测试


## ⚙️ 配置说明

### 环境变量

可以通过 HuggingFace Secrets 配置以下变量：

- `TELEGRAM_BOT_TOKEN`（必需）：你的 Telegram Bot Token
- `TELEGRAM_API_BASE`（必需）：你的 Cloudflare Worker 反代 URL（如 `https://你的域名/telegram-api`）
- `POLLING_INTERVAL`（可选，默认：`10`秒）

### 轮询间隔

当前设置为 10 秒轮询一次。根据你提到的免费账号 10 万次请求限制：
- 10 秒轮询 = 每小时 360 次
- 每天约 8,640 次
- 可以运行约 11.5 天才会达到 10 万次限制

如果需要节省额度，可以增加 `POLLING_INTERVAL` 到 30 或 60 秒。

## 📝 使用机器人

部署成功后，在 Telegram 中：

1. 搜索你的机器人（@你的机器人用户名）
2. 发送 `/start` 查看帮助
3. 发送 `/bin 551827` 查询 BIN 信息
4. 机器人会返回卡信息和生成的地址

## 🐛 故障排除

### 机器人无响应

1. 检查 Space 的 "Logs" 标签，确认机器人已启动
2. 确认 `TELEGRAM_BOT_TOKEN` 配置正确
3. 检查 Cloudflare Worker 是否正常工作

### API 请求失败

1. 测试 Cloudflare Worker：访问你的反代 URL 根路径
2. 应该看到：`Telegram API Proxy Worker - Ready to forward requests to Telegram API`
3. 确认域名路由配置正确

### 容器启动失败

1. 查看 "Build" 标签的构建日志
2. 确认所有依赖都正确安装
3. 检查 Dockerfile 语法

## 📊 监控和维护

### 查看日志
- 在 HuggingFace Space 的 "Logs" 标签查看实时日志
- 日志会显示每次收到的消息和处理结果

### 重启 Space
如果需要重启：
1. 进入 Space 设置
2. 点击 "Factory reboot"
3. 或者修改任意文件（如 README.md）并提交，触发重新构建

## 🚀 后续扩展

你提到以后可能会加功能，建议的扩展方向：

1. **批量查询**：支持一次查询多个 BIN
2. **历史记录**：保存用户查询历史
3. **更多数据源**：集成更多 BIN 数据库
4. **数据导出**：支持导出为 CSV/JSON
5. **用户管理**：白名单/黑名单功能
6. **统计分析**：查询统计和分析功能

## 📞 支持

如有问题，可以：
1. 查看 HuggingFace Spaces 文档
2. 检查本文档的故障排除部分
3. 查看代码中的注释和日志输出
