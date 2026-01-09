---
title: Telegram BIN Info Bot
emoji: 💳
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# Telegram BIN Information Bot

这是一个部署在 HuggingFace Spaces 的 Telegram 机器人，用于查询银行卡 BIN 信息并生成对应国家的地址信息。

## 功能特性

- 🔍 查询 BIN（银行识别码）信息
- 🌍 获取发卡国家、卡组织、卡类型等信息
- 📍 自动生成对应国家的随机地址信息
- 🔄 使用 Cloudflare Worker 反代 Telegram API

## 使用说明

1. 在 Telegram 中搜索你的机器人
2. 发送 `/start` 查看帮助
3. 发送 `/bin <BIN号>` 查询信息，例如：`/bin 551827`
4. 或直接发送 6-8 位数字 BIN 号

## 技术架构

- **编程语言**: Python 3.11
- **框架**: curl_cffi + BeautifulSoup
- **部署平台**: HuggingFace Spaces (Docker)
- **API 代理**: Cloudflare Worker

## 环境配置

需要在 HuggingFace Spaces 设置中配置以下 Secret：

- `TELEGRAM_BOT_TOKEN`: 你的 Telegram Bot Token
