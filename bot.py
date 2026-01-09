"""
Telegram Bot for BIN Information Lookup
部署到 HuggingFace Spaces 的 Telegram Bot
使用 Cloudflare Worker 反代 Telegram API
"""

import os
import json
import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from curl_cffi import requests as cffi_requests
from get_bininfo import BinInfoFetcher


class HealthCheckHandler(BaseHTTPRequestHandler):
    """简单的健康检查处理器 - HuggingFace Spaces 需要"""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {'status': 'ok', 'service': 'BIN Bot'}
        self.wfile.write(json.dumps(response).encode())
    
    def log_message(self, format, *args):
        # 静默日志
        pass


def start_health_server(port=7860):
    """启动健康检查服务器"""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server started on port {port}")
    server.serve_forever()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
# 使用 Cloudflare 反代的 Telegram API 地址
TELEGRAM_API_BASE = os.environ.get('TELEGRAM_API_BASE')
# 轮询间隔（秒）
POLLING_INTERVAL = int(os.environ.get('POLLING_INTERVAL', '10'))


class TelegramBot:
    """Telegram Bot 类 - 使用轮询模式"""
    
    def __init__(self, token: str, api_base: str):
        self.token = token
        self.api_base = api_base.rstrip('/')
        self.session = cffi_requests.Session(impersonate="Chrome124")
        self.offset = 0
        self.bin_fetcher = BinInfoFetcher()
        
    def _make_request(self, method: str, data: dict = None) -> dict:
        """向 Telegram API 发送请求"""
        url = f"{self.api_base}/bot{self.token}/{method}"
        try:
            if data:
                resp = self.session.post(url, json=data, timeout=30)
            else:
                resp = self.session.get(url, timeout=30)
            
            result = resp.json()
            if not result.get('ok'):
                logger.error(f"API Error: {result}")
            return result
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {'ok': False, 'error': str(e)}
    
    def get_updates(self) -> list:
        """获取新消息"""
        result = self._make_request('getUpdates', {
            'offset': self.offset,
            'timeout': 5,
            'allowed_updates': ['message']
        })
        
        if result.get('ok'):
            updates = result.get('result', [])
            if updates:
                # 更新 offset 为最新消息 ID + 1
                self.offset = updates[-1]['update_id'] + 1
            return updates
        return []
    
    def send_message(self, chat_id: int, text: str, parse_mode: str = 'HTML') -> dict:
        """发送消息"""
        return self._make_request('sendMessage', {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        })
    
    def format_bin_result(self, result: dict) -> str:
        """格式化 BIN 查询结果"""
        bin_info = result.get('bin_info', {})
        billing = result.get('billing', {})
        
        text = "🏦 <b>BIN 信息</b>\n"
        text += "━━━━━━━━━━━━━━━\n"
        text += f"🌍 国家: {bin_info.get('country', 'N/A')} ({bin_info.get('country_code', 'N/A')})\n"
        text += f"💳 卡组织: {bin_info.get('card_brand', 'N/A')}\n"
        text += f"📋 卡类型: {bin_info.get('card_type', 'N/A')}\n"
        text += f"🏛️ 发卡行: {bin_info.get('bank', 'N/A')}\n"
        
        text += "\n📍 <b>生成地址</b>\n"
        text += "━━━━━━━━━━━━━━━\n"
        text += f"👤 姓名: <code>{billing.get('name', 'N/A')}</code>\n"
        text += f"🏠 地址: <code>{billing.get('address_line1', 'N/A')}</code>\n"
        text += f"🏙️ 城市: <code>{billing.get('city', 'N/A')}</code>\n"
        text += f"📮 邮编: <code>{billing.get('postal_code', 'N/A')}</code>\n"
        text += f"📞 电话: <code>{billing.get('phone', 'N/A')}</code>\n"
        text += f"📧 邮箱: <code>{billing.get('email', 'N/A')}</code>\n"
        
        return text
    
    def handle_message(self, message: dict):
        """处理收到的消息"""
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        logger.info(f"Received message from {chat_id}: {text}")
        
        # /start 命令
        if text.startswith('/start'):
            welcome_text = """
👋 <b>欢迎使用 BIN 信息查询机器人!</b>

📌 <b>使用方法:</b>
• 发送 /bin &lt;BIN号&gt; 查询卡信息和生成地址
• 例如: <code>/bin 551827</code>

📌 <b>命令列表:</b>
• /start - 显示帮助信息
• /bin &lt;BIN&gt; - 查询 BIN 信息

💡 BIN 号是银行卡的前 6-8 位数字
"""
            self.send_message(chat_id, welcome_text)
            return
        
        # /help 命令
        if text.startswith('/help'):
            help_text = """
📖 <b>帮助信息</b>

🔍 <b>什么是 BIN?</b>
BIN (Bank Identification Number) 是银行卡的前 6-8 位数字，用于识别发卡银行和卡类型。

📌 <b>如何使用:</b>
发送 /bin 加上 BIN 号即可查询
例如: <code>/bin 551827</code>

🔄 <b>返回信息包括:</b>
• 发卡国家和代码
• 卡组织 (Visa/Mastercard/...)
• 卡类型 (Credit/Debit)
• 发卡银行
• 随机生成的对应国家地址
"""
            self.send_message(chat_id, help_text)
            return
        
        # /bin 命令
        if text.startswith('/bin'):
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                self.send_message(chat_id, "❌ 请提供 BIN 号\n例如: <code>/bin 551827</code>")
                return
            
            bin_number = parts[1].strip()
            
            # 验证 BIN 格式
            if not bin_number.isdigit() or len(bin_number) < 6:
                self.send_message(chat_id, "❌ BIN 号格式错误，请输入至少 6 位数字")
                return
            
            # 发送 "正在查询" 提示
            self.send_message(chat_id, f"🔄 正在查询 BIN: <code>{bin_number[:6]}</code>...")
            
            try:
                # 查询 BIN 信息
                result = self.bin_fetcher.get_billing_info(bin_number[:8])
                
                if result:
                    response_text = self.format_bin_result(result)
                    self.send_message(chat_id, response_text)
                else:
                    self.send_message(chat_id, f"❌ 未找到 BIN <code>{bin_number[:6]}</code> 的信息")
                    
            except Exception as e:
                logger.error(f"Error querying BIN: {e}")
                self.send_message(chat_id, f"❌ 查询出错: {str(e)}")
            
            return
        
        # 处理直接发送的数字（假定为 BIN）
        if text.strip().isdigit() and len(text.strip()) >= 6:
            bin_number = text.strip()
            self.send_message(chat_id, f"🔄 正在查询 BIN: <code>{bin_number[:6]}</code>...")
            
            try:
                result = self.bin_fetcher.get_billing_info(bin_number[:8])
                
                if result:
                    response_text = self.format_bin_result(result)
                    self.send_message(chat_id, response_text)
                else:
                    self.send_message(chat_id, f"❌ 未找到 BIN <code>{bin_number[:6]}</code> 的信息")
                    
            except Exception as e:
                logger.error(f"Error querying BIN: {e}")
                self.send_message(chat_id, f"❌ 查询出错: {str(e)}")
            
            return
        
        # 未知命令
        self.send_message(chat_id, "❓ 未知命令\n发送 /start 查看帮助")
    
    def run(self):
        """运行机器人（轮询模式）"""
        logger.info("Bot starting...")
        logger.info(f"API Base: {self.api_base}")
        logger.info(f"Polling interval: {POLLING_INTERVAL} seconds")
        
        # 测试连接
        me = self._make_request('getMe')
        if me.get('ok'):
            bot_info = me.get('result', {})
            logger.info(f"Bot connected: @{bot_info.get('username', 'unknown')}")
        else:
            logger.error(f"Failed to connect: {me}")
            return
        
        # 开始轮询
        while True:
            try:
                updates = self.get_updates()
                
                for update in updates:
                    if 'message' in update:
                        self.handle_message(update['message'])
                
                # 等待指定间隔
                time.sleep(POLLING_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(POLLING_INTERVAL)


def main():
    """主函数"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    if not TELEGRAM_API_BASE:
        logger.error("TELEGRAM_API_BASE environment variable not set!")
        return
    
    # 启动健康检查服务器（后台线程）
    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()
    
    # 启动机器人
    bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_API_BASE)
    bot.run()


if __name__ == '__main__':
    main()
