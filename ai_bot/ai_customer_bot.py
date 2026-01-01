"""
AI Customer Support Bot - Telegram бот с AI для ответов клиентам
Использует Google Gemini API и pyTelegramBotAPI
"""

import os
import sys
import telebot
from telebot import types
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging
import traceback
import requests
import json

from ai_bot.ai_engine import MonaAI

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Загрузка переменных окружения
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

class AICustomerBot:
    """Mona v7.0 - Telegram Интерфейс элитного бутика Monvoir"""
    
    def __init__(self, bot_token, gemini_key):
        self.bot = telebot.TeleBot(bot_token)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("MonaBot")
        
        # Инициализация ИИ-движка (Набор готовых функций)
        self.ai = MonaAI()
        
        self.sessions = {}
        self.ADMIN_ID = 5644397480
        self.waiting_for_support = set()
        self._register_handlers()

    def _get_session(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {'history': [], 'last_active': datetime.now()}
        return self.sessions[user_id]

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def welcome(m):
            session = self._get_session(m.from_user.id)
            session['history'] = []
            msg = "✨ <b>Mona v7.0 приветствует Вас!</b>\nЧем я могу быть полезна сегодня?"
            self.bot.send_message(m.chat.id, msg, parse_mode='HTML')

        @self.bot.message_handler(commands=['manager'])
        def manager(m):
            self.waiting_for_support.add(m.from_user.id)
            self.bot.send_message(m.chat.id, "👨‍💼 Напишите Ваш вопрос менеджеру.")

        @self.bot.message_handler(func=lambda m: m.chat.id == self.ADMIN_ID and m.reply_to_message)
        def admin_reply(m):
            try:
                self.bot.send_message(m.reply_to_message.forward_from.id, f"👨‍💼 <b>Ответ менеджера:</b>\n\n{m.text}", parse_mode='HTML')
                self.bot.reply_to(m, "✅ Отправлено.")
            except: self.bot.reply_to(m, "❌ Ошибка отправки.")

        @self.bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            user_id = m.from_user.id
            if user_id in self.waiting_for_support:
                self.bot.forward_message(self.ADMIN_ID, m.chat.id, m.message_id)
                self.waiting_for_support.remove(user_id)
                self.bot.send_message(m.chat.id, "✅ Отправлено.")
                return

            session = self._get_session(user_id)
            user_text = m.text or "[Фото]"
            self.bot.send_chat_action(m.chat.id, 'typing')

            # 1. Формируем контекст
            messages = session['history'][-8:]
            messages.append({"role": "user", "content": user_text})

            try:
                # ЦИКЛ ОРКЕСТРАЦИИ (Request -> See -> Think -> Respond)
                iteration = 0
                final_data = {"response": "✨ Я уточняю информацию..."}
                
                while iteration < 3:
                    iteration += 1
                    # A. Запрос к ИИ (Get Information Request)
                    ai_json = self.ai.generate(messages)
                    if not ai_json: break
                    
                    final_data = ai_json
                    action = ai_json.get("action", {})
                    
                    # B. Проверка, нужно ли действие (Act)
                    if not action or action.get("tool") == "none":
                        break
                        
                    # C. Получение данных (See)
                    result = self.ai.execute_action(action, session)
                    self.logger.info(f"Mona v7.0 Data Result: {result[:50]}...")
                    
                    # D. Добавление данных в контекст для "обдумывания" (Think)
                    messages.append({"role": "assistant", "content": json.dumps(ai_json, ensure_ascii=False)})
                    messages.append({"role": "user", "content": f"SYSTEM_RESULT: {result}"})
                
                # 2. Финальное оформление ответа (UI Format)
                resp_text = final_data.get("response", "✨")
                formatted_resp = self.ai.format_ui(resp_text, session)

                # 3. Отправка и сохранение истории
                self.bot.send_message(m.chat.id, formatted_resp, parse_mode='HTML', disable_web_page_preview=True)
                session['history'].append({"role": "user", "content": user_text})
                session['history'].append({"role": "assistant", "content": json.dumps(final_data, ensure_ascii=False)})
                
            except Exception as e:
                self.logger.error(f"Handle Error: {e}")
                self.bot.send_message(m.chat.id, "✨ Произошла небольшая заминка. Повторите запрос.")

    def run(self):
        print("💎 Mona v7.0: The Rebirth запущен")
        self.bot.infinity_polling()

def main():
    bot_token = os.getenv('AI_BOT_TOKEN')
    gemini_key = os.getenv('GEMINI_API_KEY')
    if bot_token:
        bot = AICustomerBot(bot_token, gemini_key)
        bot.run()

if __name__ == "__main__":
    main()
