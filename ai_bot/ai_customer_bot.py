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

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ЯВНЫЙ ВЫВОД ВЕРСИИ ДЛЯ ОТЛАДКИ
print("🚀 ЗАПУСК БОТА: ВЕРСИЯ 3.1 (GROQ INTEGRATION)", flush=True)

import re
from ai_bot.ai_db_helper import get_all_products_info, search_products, format_products_for_ai, get_order_status

# Загрузка переменных окружения (явно указываем путь)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

print(f"DEBUG: CWD = {os.getcwd()}", flush=True)
print(f"DEBUG: .env path = {env_path}", flush=True)
print(f"DEBUG: GROQ_API_KEY present = {bool(os.getenv('GROQ_API_KEY'))}", flush=True)


class AICustomerBot:
    """Класс AI бота для обслуживания клиентов"""
    
    def __init__(self, bot_token, gemini_key):
        """
        Инициализация бота
        
        Args:
            bot_token (str): Telegram Bot API токен
        """
        self.bot = telebot.TeleBot(bot_token)
        
        # Инициализация Groq клиента
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            print("⚠️ GROQ_API_KEY не найден в .env! AI не будет работать.")
            self.client = None
        else:
            try:
                self.client = Groq(api_key=self.api_key)
                self.model_name = "llama-3.3-70b-versatile"
                print(f"✅ Модель: Groq {self.model_name} подключена", flush=True)
            except Exception as e:
                print(f"⚠️ Ошибка инициализации Groq: {e}", flush=True)
                self.client = None
        
        # Хранилище сессий: {user_id: {'history': [], 'last_active': datetime}}
        self.sessions = {}
        self.SESSION_TIMEOUT = timedelta(hours=6)
        
        # Поддержка (Manager)
        self.ADMIN_ID = 5644397480
        self.waiting_for_support = set()
        self.waiting_for_search = set()
        self.support_messages = {}
        
        # Системный промпт для AI
        self.system_prompt = """
Ты — Mona, AI-консультант магазина мужской одежды "Monvoir".
Сайт: https://monvoir.shop

ТВОЯ ЦЕЛЬ: Помочь клиенту найти товар в магазине, узнать статус заказа или позвать менеджера.

⛔️ СТРОЖАЙШИЙ ЗАПРЕТ НА БОЛТОВНЮ (OFF-TOPIC):
- Ты НЕ общаешься на отвлеченные темы (погода, политика, философия, физика, диаметр Земли и т.д.).
- Если вопрос не про одежду, заказ или магазин — вежливо откажи.
- Пример отказа: "Я специализируюсь только на мужской моде и нашем ассортименте. Подсказать что-то по одежде? 👔"

ПРАВИЛА ПО КОНТЕНТУ:
1. **ТОЛЬКО ТОВАРЫ ИЗ БАЗЫ:**
   - Отвечай только по тем данным, которые я тебе прислал в разделе "ИНФОРМАЦИЯ О ТОВАРАХ".
   - Если товара нет в списке — значит его нет. Не выдумывай.

2. **БАЗА ЗНАНИЙ (ОТВЕТЫ НА ВОПРОСЫ):**
   - **🚚 ДОСТАВКА:**
     - Ташкент: 24 часа. (Быстро и бережно).
     - Регионы (Узбекистан): 2-3 дня (BTS/Fargo).
     - Если спрашивают про доставку конкретного товара (по ID) — подтверждай, что мы доставим его в любую точку.
   
   - **📍 НАВИГАЦИЯ:**
     - "Где найти?": Скажи "Перейдите в Каталог на сайте".
     - "Как купить?": "1. Выберите размер -> 2. В корзину -> 3. Оплатите".
   
   - **💳 ОПЛАТА:** Click, Payme, Наличные (только Ташкент).
   
   - **🔄 ВОЗВРАТ И ДЕНЬГИ:** 
     - 🛑 ТЫ НЕ РЕШАЕШЬ ВОПРОСЫ ВОЗВРАТА ДЕНЕГ!
     - 🛑 ТЫ НЕ ЗНАЕШЬ ПОЛИТИКУ ВОЗВРАТА В ДЕТАЛЯХ.
     - Если клиент спрашивает "Верните деньги", "Как сделать возврат", "Где мои деньги" — СРАЗУ отправляй к менеджеру (/manager). Это строго.

3. **ССЫЛКИ И ЦВЕТА:**
   - Название товара = Ссылка (<a href="..."><b>Название</b></a>).
   - Hex-коды (#000000) — ЗАПРЕЩЕНЫ. Пиши словами: "Черный", "Хаки".

4. **ЛОГИКА ОТВЕТА (СТРОГО):**
   - **ОТВЕЧАЙ ТОЛЬКО НА ЗАДАННЫЙ ВОПРОС.**
   - Не добавляй лишней информации, если не просили.
   - Если спросили "Где мой заказ?" -> ответь только про статус и дату. Не предлагай купить носки.
   - Если тебе дали ИНФОРМАЦИЮ О ЗАКАЗЕ — используй её.

ПРИМЕРЫ:
(Вопрос): "Где мой заказ?"
(Ответ): "Ваш заказ в пути! 🚚 Ожидаемая доставка до 30.12.2025. Курьер позвонит."
(НЕПРАВИЛЬНО): "Ваш заказ в пути. А еще посмотрите наши новые шарфы..." (ЗАПРЕЩЕНО)

(Вопрос про деньги): "Верните мне деньги за заказ!"
(Ответ): "Финансовые вопросы решает только администратор. Пожалуйста, напишите /manager, он поможет! 👨‍💼"

(Вопрос про доставку): "Как долго ждать доставку пиджака?"
(Ответ): "По Ташкенту доставим за сутки! 🚀 В регионы — 2-3 дня. Оформим?"
"""
        
        # Регистрация обработчиков
        self._register_handlers()
    
    def _get_user_session(self, user_id):
        """Получает или создает сессию пользователя с проверкой тайм-аута"""
        now = datetime.now()
        
        if user_id in self.sessions:
            session = self.sessions[user_id]
            # Проверка тайм-аута (6 часов)
            if now - session['last_active'] > self.SESSION_TIMEOUT:
                # Сессия устарела, сбрасываем
                self.sessions[user_id] = {'history': [], 'last_active': now}
                return self.sessions[user_id]
            
            # Обновляем время активности
            session['last_active'] = now
            return session
        
        # Новая сессия
        self.sessions[user_id] = {'history': [], 'last_active': now}
        return self.sessions[user_id]

    def _format_history_for_prompt(self, history):
        """Форматирует историю переписки для AI"""
        if not history:
            return ""
        
        conversation_text = "\nИСТОРИЯ ПЕРЕПИСКИ:\n"
        for msg in history[-10:]: # Берем последние 10 сообщений
            role = "КЛИЕНТ" if msg['role'] == 'user' else "ТЫ (БОТ)"
            conversation_text += f"{role}: {msg['text']}\n"
        
        return conversation_text

    def _register_handlers(self):
        """Регистрация обработчиков команд и сообщений"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            """Обработка команды /start"""
            user_id = message.from_user.id
            username = message.from_user.first_name or "друг"
            
            # Сброс сессии при старте
            self.sessions[user_id] = {'history': [], 'last_active': datetime.now()}
            
            welcome_text = f"""
👋 Привет, <b>{username}</b>!

Я - <b>Мона</b>, AI помощник магазина Monvoir. Могу ответить на вопросы о товарах:

• Какие товары есть в наличии?
• Какие цвета/размеры доступны?
• Сколько стоит товар?
• Какие товары есть в наличии?
• Какие цвета/размеры доступны?
• Какие товары есть в наличии?
• Какие цвета/размеры доступны?
• Сколько стоит товар?
• Что есть в конкретной категории?
• /search - поиск по фото
• /manager - позвать человека

Просто напишите свой вопрос! 💬
"""
            try:
                self.bot.send_message(message.chat.id, welcome_text, parse_mode='HTML')
            except Exception:
                self.bot.send_message(message.chat.id, welcome_text) # Fallback без HTML
        
        @self.bot.message_handler(commands=['manager'])
        def handle_manager(message):
            """Обработка команды /manager"""
            user_id = message.from_user.id
            self.waiting_for_support.add(user_id)
            if user_id in self.waiting_for_search: self.waiting_for_search.remove(user_id)
            
            self.bot.send_message(
                message.chat.id, 
                "👨‍💼 <b>Связь с менеджером</b>\n\n"
                "Напишите ваш вопрос, и я перешлю его администратору.", 
                parse_mode='HTML'
            )

        @self.bot.message_handler(commands=['search'])
        def handle_search(message):
            """Обработка команды /search"""
            user_id = message.from_user.id
            self.waiting_for_search.add(user_id)
            if user_id in self.waiting_for_support: self.waiting_for_support.remove(user_id)
            
            self.bot.send_message(
                message.chat.id,
                "📸 <b>Поиск по фото</b>\n\n"
                "Отправьте фотографию товара, и менеджер проверит его наличие.",
                parse_mode='HTML'
            )
            
        @self.bot.message_handler(func=lambda m: m.chat.id == self.ADMIN_ID and m.reply_to_message)
        def handle_admin_reply(message):
            """Обработка ответа админа на пересланное сообщение"""
            reply_to_id = message.reply_to_message.message_id
            
            if reply_to_id in self.support_messages:
                target_user_id = self.support_messages[reply_to_id]
                
                try:
                    self.bot.send_message(
                        target_user_id,
                        f"👨‍💼 <b>Ответ менеджера:</b>\n\n{message.text}",
                        parse_mode='HTML'
                    )
                    self.bot.reply_to(message, "✅ Ответ отправлен пользователю.")
                except Exception as e:
                    self.bot.reply_to(message, f"❌ Не удалось отправить ответ: {e}")
            else:
                # Если админ отвечает просто так, или бот был перезагружен и память очистилась
                pass 

        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            """Обработка команды /help"""
            help_text = """
ℹ️ <b>Как пользоваться ботом:</b>

Просто задавайте вопросы на естественном языке!

<b>Примеры вопросов:</b>
• Какие товары у вас есть?
• Покажи футболки
• Есть ли черные кроссовки?
• Какие размеры доступны?
• Сколько стоит Nike Pro?

Команды:
/search - Поиск товара по фото
/manager - Позвать живого менеджера

Я отвечу на основе актуальной информации из базы данных! 🤖
"""
            self.bot.send_message(message.chat.id, help_text, parse_mode='HTML')
        
        @self.bot.message_handler(content_types=['text', 'photo'])
        def handle_question(message):
            """Обработка вопросов от клиентов"""
            user_id = message.from_user.id
            user_question = message.text
            
            # 1. Проверка: Ждем ли мы сообщение для менеджера или поиска?
            if user_id in self.waiting_for_support or user_id in self.waiting_for_search:
                self._forward_to_admin(message, "Поиск по фото" if user_id in self.waiting_for_search else "Запрос менеджера")
                return

            # Проверка на запрос статуса заказа (regex)
            # Поддержка UUID и обычных ID (буквы, цифры, дефисы)
            order_match = re.search(r'(заказ|статус|order|id)\s*[:#№]?\s*([A-Za-z0-9\-]{5,})', user_question.lower())
            if order_match:
                order_id = order_match.group(2)
                status_info = get_order_status(order_id)
                if status_info:
                    self.bot.send_message(message.chat.id, f"📦 {status_info}")
                    return
                else:
                    self.bot.send_message(
                        message.chat.id, 
                        f"🚫 <b>ID заказа {order_id} не найден.</b>\n"
                        "Пожалуйста, проверьте ID. Вы можете найти его в личном кабинете на сайте.",
                        parse_mode='HTML'
                    )
                    return
            
            # Получаем сессию
            session = self._get_user_session(user_id)
            
            # Отправляем индикатор "печатает..."
            self.bot.send_chat_action(message.chat.id, 'typing')
            
            try:
                # 2. Получаем контекст товаров
                products_context = "Информацию о товарах пока получить не удалось."
                try:
                    # Поиск, если вопрос о конкретном товаре
                    if any(word in user_question.lower() for word in ['найди', 'покажи', 'есть ли', 'цена', 'сколько']):
                         # Простой поиск по ключевым словам из вопроса
                        found_products = search_products(user_question)
                        if found_products:
                             products_context = format_products_for_ai(found_products[:5])
                        else:
                            # Если ничего не нашли, берем общие товары
                            all_products = get_all_products_info()
                            products_context = format_products_for_ai(all_products[:10])
                    else:
                        # По умолчанию показываем топ товаров
                        all_products = get_all_products_info()
                        products_context = format_products_for_ai(all_products[:10])
                except Exception as e:
                    print(f"⚠️ Ошибка получения товаров: {e}")

                # 3. Проверка на статус заказа
                order_info = ""
                # Нормализация: убираем # и заменяем кириллицу
                clean_question = user_question.lower().replace('#', '').translate(str.maketrans("асеорх", "aceopx"))
                
                # Ищем полный UUID или короткий ID
                uuid_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
                short_id_pattern = r'\b[0-9a-f]{6,}\b'
                
                found_uuids = re.findall(uuid_pattern, clean_question)
                if not found_uuids:
                    found_uuids = re.findall(short_id_pattern, clean_question)
                
                if found_uuids:
                    order_id = found_uuids[0]
                    status_result = get_order_status(order_id)
                    if status_result:
                        order_info = f"\n\nИНФОРМАЦИЯ О ЗАКАЗЕ:\n{status_result}\n(Используй эту информацию, чтобы ответить клиенту)"
                    else:
                        # Диагностика для пользователя: анализируем ошибку
                        parts = order_id.split('-')
                        hint = ""
                        if len(parts) > 0 and len(parts[0]) != 8:
                            hint = f" (Обычно первая часть номера состоит из 8 символов, а у вас {len(parts[0])}. Проверьте, нет ли лишней цифры?)"
                        elif len(order_id) < 6:
                            hint = " (Номер слишком короткий.)"
                            
                        order_info = f"\n\nИНФОРМАЦИЯ О ЗАКАЗЕ:\nЯ искала заказ по номеру '{order_id}', но не нашла его.{hint} Пожалуйста, сверьте номер с сайтом."
                
                # Генерируем ответ
                try:
                    if self.client:
                        # Подготовка сообщений для Groq
                        messages = [
                            {"role": "system", "content": f"{self.system_prompt}\n\nИНФОРМАЦИЯ О ТОВАРАХ:\n{products_context}\n\n{order_info if order_info else ''}"}
                        ]
                        
                        # Добавляем историю переписки
                        # history в self.sessions хранит {'role': 'user'/'model', 'text': ...} - нужно адаптировать под API Groq
                        # Groq ожидает 'role': 'user' или 'assistant'
                        for msg in session['history'][-10:]: # последние 10 сообщений
                            role = "user" if msg['role'] == "user" else "assistant"
                            messages.append({"role": role, "content": msg['text']})
                        
                        # Добавляем текущий вопрос
                        messages.append({"role": "user", "content": user_question})

                        # Вызов API
                        completion = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=messages,
                            temperature=0.8, # Чуть выше для "живости" Моны
                            max_tokens=1024,
                            top_p=1,
                            stop=None,
                            stream=False
                        )
                        
                        response_text = completion.choices[0].message.content
                         
                        if response_text:
                             # Отправляем ответ клиенту
                             try:
                                 self.bot.send_message(
                                     message.chat.id,
                                     response_text,
                                     parse_mode='HTML'
                                 )
                             except Exception as e:
                                 print(f"⚠️ Ошибка отправки (HTML): {e}")
                                 # Пробуем без Markdown/HTML если ошибка парсинга
                                 self.bot.send_message(message.chat.id, response_text)
                                 
                             # Сохраняем в историю
                             self._update_history(user_id, user_question, response_text)
                        else:
                             raise Exception("Пустой ответ от модели")
                    else:
                        raise Exception("Модель не инициализирована (self.client is None)")
                        
                except Exception as e:
                     raise e  # Пробрасываем ошибку выше
                    
            except Exception as e:
                error_msg = f"❌ Ошибка генерации: {e}"
                print(error_msg, flush=True)
                
                # ОТЛАДКА: Отправляем текст ошибки прямо в чат, чтобы пользователь увидел его
                self.bot.send_message(message.chat.id, f"DEBUG ERROR: {e}")

                # Fallback: Если есть информация о заказе...
                if order_info and "ИНФОРМАЦИЯ О ЗАКАЗЕ" in order_info and "не найден" not in order_info:
                    try:
                        clean_info = order_info.replace("\n\nИНФОРМАЦИЯ О ЗАКАЗЕ:\n", "").replace("\n(Используй эту информацию, чтобы ответить клиенту о статусе его заказа)", "")
                        self.bot.send_message(
                            message.chat.id,
                            f"🤖 <b>Автоматический ответ:</b>\n\n{clean_info}\n\n<i>(AI временно недоступен, но я нашел ваш заказ в базе)</i>",
                            parse_mode='HTML'
                        )
                        return
                    except Exception:
                        pass

                self.bot.send_message(
                    message.chat.id,
                    "😔 Извините, произошла техническая ошибка или сеть перегружена.\n"
                    "Попробуйте позже или свяжитесь с менеджером через /manager."
                )
    
    def _update_history(self, user_id, user_text, bot_text):
        """Обновление истории сообщений"""
        if user_id not in self.sessions:
            self._get_user_session(user_id)
            
        session = self.sessions[user_id]
        session['history'].append({'role': 'user', 'text': user_text})
        session['history'].append({'role': 'model', 'text': bot_text})
        
        # Ограничиваем историю (последние 20 сообщений)
        if len(session['history']) > 20:
            session['history'] = session['history'][-20:]
            
        session['last_active'] = datetime.now()
    
    def _forward_to_admin(self, message, request_type):
        """Вспомогательный метод пересылки админу"""
        user_id = message.from_user.id
        try:
            username = message.from_user.username or "Без юзернейма"
            
            self.bot.send_message(
                self.ADMIN_ID,
                f"📩 <b>{request_type}</b>\n"
                f"От: @{username} (ID: <code>{user_id}</code>)\n"
                f"👇 Ответьте на сообщение ниже:",
                parse_mode='HTML'
            )
            
            fwd_msg = self.bot.forward_message(self.ADMIN_ID, message.chat.id, message.message_id)
            self.support_messages[fwd_msg.message_id] = user_id
            
            # Очистка состояния
            if user_id in self.waiting_for_support: self.waiting_for_support.remove(user_id)
            if user_id in self.waiting_for_search: self.waiting_for_search.remove(user_id)
            
            self.bot.send_message(message.chat.id, "✅ Запрос отправлен менеджеру. Ожидайте ответа.")
        except Exception as e:
            print(f"❌ Ошибка Forward: {e}")
            self.bot.send_message(message.chat.id, "Ошибка отправки.")

    def run(self):
        """Запуск бота в режиме polling"""
        print("🤖 AI Customer Bot запущен и готов к работе (v2.1 STABLE)...")
        print("✅ Модель: Gemini 2.0 Flash (If check failed, used fallback)")
        print("✅ Память: включена (тайм-аут 6 часов)")
        print(f"📊 Бот: @{self.bot.get_me().username}")
        
        # Бесконечный цикл с перезапуском при падении сети
        while True:
            try:
                self.bot.infinity_polling(timeout=60, long_polling_timeout=5)
            except Exception as e:
                print(f"⚠️ Ошибка сети, перезапуск через 5 секунд: {e}")
            
            # Пауза перед перезапуском, даже если ошибки не было (защита от спама)
            import time
            time.sleep(5)


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
