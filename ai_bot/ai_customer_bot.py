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

# ЯВНЫЙ ВЫВОД ВЕРСИИ ДЛЯ ОТЛАДКИ
print("🚀 ЗАПУСК БОТА: ВЕРСИЯ 7.0 (THE REBIRTH)", flush=True)

import re
from ai_bot.ai_db_helper import (
    get_all_products_info, search_products, format_products_for_ai, 
    get_order_status, get_product_details, get_catalog_titles, get_pretty_product_info
)

# Загрузка переменных окружения
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

class AICustomerBot:
    """Mona v7.0 - Элитный AI-движок бутика Monvoir"""
    
    def __init__(self, bot_token, gemini_key):
        self.bot = telebot.TeleBot(bot_token)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.FileHandler("ai_bot.log", encoding='utf-8'), logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger("Mona7")
        
        # Интеграция Groq (Основное сердце)
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.groq = Groq(api_key=self.groq_key) if self.groq_key else None
        
        # Интеграция Gemini (Запасной интеллект)
        self.gemini_key = gemini_key
        
        self.sessions = {}
        self.ADMIN_ID = 5644397480
        self.waiting_for_support = set()
        self.waiting_for_search = set()
        self.support_messages = {}

        self.system_prompt = """
### 💎 MONA v7.0: ЭЛИТНЫЙ ПРОТОКОЛ
Ты — Mona, голос бренда Monvoir. Твой интеллект работает на данных, а стиль — на безупречности.

#### 📤 ФОРМАТ ОТВЕТА (JSON):
Ты всегда отвечаешь ТОЛЬКО структурированным JSON:
{
  "thoughts": "Твоя стратегия (почему ты делаешь это действие).",
  "action": { "tool": "search|info|catalog|order", "args": { "query": "str", "id": "id" } },
  "response": "Итоговый, роскошный ответ для клиента (используй [ИНФО:id], [ТОВАРЫ:0,5], [ЗАКАЗ:id])."
}

#### 🛠 ИНСТРУМЕНТЫ:
- `search`: Поиск ID товаров.
- `info`: Детальные данные из базы (наличие, размеры). **Всегда проверяй info перед тем как подтвердить наличие.**
- `catalog`: Список всех категорий.
- `order`: Проверка статуса заказа.

#### 🎨 ПРАВИЛА БРЕНДА:
- Не используй [ТОВАРЫ], если не уверена в ID.
- Если товара нет, предложи альтернативу из той же категории.
- Никогда не упоминай технические детали (JSON, ID) в поле 'response'.
"""
        self._register_handlers()

    def _get_session(self, user_id):
        if user_id not in self.sessions:
            self.sessions[user_id] = {'history': [], 'last_active': datetime.now(), 'greeted': False}
        return self.sessions[user_id]

    def _call_ai(self, messages):
        """Прямой вызов Groq с мгновенным ответом"""
        try:
            if not self.groq: return None
            completion = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            return completion.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Groq Error: {e}")
            # Fallback на Gemini через requests (упрощенно)
            return None

    def _extract_json(self, text):
        try:
            return json.loads(text)
        except:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                try: return json.loads(match.group(1))
                except: pass
        return None

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def welcome(m):
            session = self._get_session(m.from_user.id)
            session['history'] = []
            msg = "✨ <b>Mona v7.0 приветствует Вас!</b>\n\nЯ Ваш персональный гид в мире Monvoir. Чем я могу быть полезна сегодня? 👗👔"
            self.bot.send_message(m.chat.id, msg, parse_mode='HTML')

        @self.bot.message_handler(commands=['manager'])
        def manager(m):
            self.waiting_for_support.add(m.from_user.id)
            self.bot.send_message(m.chat.id, "👨‍💼 Напишите Ваш вопрос, и я передам его менеджеру.")

        @self.bot.message_handler(content_types=['text', 'photo'])
        def handle(m):
            user_id = m.from_user.id
            if user_id in self.waiting_for_support:
                self.bot.forward_message(self.ADMIN_ID, m.chat.id, m.message_id)
                self.waiting_for_support.remove(user_id)
                self.bot.send_message(m.chat.id, "✅ Ваш запрос отправлен.")
                return

            session = self._get_session(user_id)
            user_text = m.text or "[Фото]"
            self.bot.send_chat_action(m.chat.id, 'typing')

            messages = [{"role": "system", "content": self.system_prompt}]
            for h in session['history'][-8:]: messages.append(h)
            messages.append({"role": "user", "content": user_text})

            try:
                iteration = 0
                final_json = {}
                while iteration < 3:
                    iteration += 1
                    raw = self._call_ai(messages)
                    data = self._extract_json(raw) if raw else None
                    if not data: break
                    
                    final_json = data
                    action = data.get("action", {})
                    tool = action.get("tool")
                    
                    if not tool or tool == "none": break
                    
                    # Выполнение инструментов
                    result = "Data not found."
                    if tool == "search":
                        res = search_products(action.get("args", {}).get("query", ""))
                        session['last_results'] = res
                        result = f"FOUND_IDS: {[{'id':p['id'], 'name':p['name']} for p in res]}"
                    elif tool == "info":
                        res = get_product_details(action.get("args", {}).get("id", ""))
                        result = format_products_for_ai([res]) if res else "Not found."
                    elif tool == "catalog":
                        result = str(get_catalog_titles())
                    elif tool == "order":
                        result = get_order_status(action.get("args", {}).get("id", ""))

                    self.logger.info(f"Mona v7.0 Tool [{tool}]: {result[:100]}...")
                    messages.append({"role": "assistant", "content": json.dumps(data, ensure_ascii=False)})
                    messages.append({"role": "user", "content": f"SYSTEM_RESULT: {result}"})
                
                # Пост-процессинг ответа
                resp = final_json.get("response", "✨ Я уточняю информацию...")
                
                # Замена тегов [ИНФО:id]
                for match in re.findall(r'\[ИНФО:([^\]]+)\]', resp):
                    resp = resp.replace(f"[ИНФО:{match}]", get_pretty_product_info(match.strip()))
                
                # Замена тегов [ТОВАРЫ:start,stop]
                tag_tov = re.search(r'\[ТОВАРЫ:(\d+),(\d+)\]', resp)
                if tag_tov:
                    start, stop = int(tag_tov.group(1)), int(tag_tov.group(2))
                    from ai_bot.ai_customer_bot import AICustomerBot as Dummy
                    # Используем старую логику форматирования списка для красоты
                    from ai_bot.ai_customer_bot import AICustomerBot
                    temp_bot = AICustomerBot(os.getenv('AI_BOT_TOKEN'), "")
                    list_text = temp_bot._get_formatted_products(session.get('last_results', []), start, stop-start)
                    resp = resp.replace(tag_tov.group(0), list_text or "Цены и наличие уточняйте у менеджера.")

                self.bot.send_message(m.chat.id, resp, parse_mode='HTML', disable_web_page_preview=True)
                session['history'].append({"role": "user", "content": user_text})
                session['history'].append({"role": "assistant", "content": json.dumps(final_json, ensure_ascii=False)})
                
            except Exception as e:
                self.logger.error(f"Handle Error: {e}")
                self.bot.send_message(m.chat.id, "✨ Произошла небольшая заминка. Повторите запрос через секунду.")

    def run(self):
        print("💎 Mona v7.0: The Rebirth запущен")
        self.bot.infinity_polling()


def main():
    """Главная функция запуска бота"""
    # Получаем токены из переменных окружения
    bot_token = os.getenv('AI_BOT_TOKEN')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    if not bot_token:
        print("❌ ОШИБКА: AI_BOT_TOKEN не найден в переменных окружения!")
        return
    
    if not gemini_key:
        print("❌ ОШИБКА: GEMINI_API_KEY не найден в переменных окружения!")
        return
    
    # Создаем и запускаем бота
    try:
        bot = AICustomerBot(bot_token, gemini_key)
        bot.run()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")


if __name__ == "__main__":
    main()
