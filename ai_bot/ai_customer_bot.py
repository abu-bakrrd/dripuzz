"""
AI Customer Support Bot - Telegram бот с AI для ответов клиентам
Использует Google Gemini API и pyTelegramBotAPI
"""

import os
import sys
import telebot
from telebot import types
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from ai_bot.ai_db_helper import get_all_products_info, search_products, format_products_for_ai, get_order_status

# Загрузка переменных окружения
load_dotenv()


class AICustomerBot:
    """Класс AI бота для обслуживания клиентов"""
    
    def __init__(self, bot_token, gemini_key):
        """
        Инициализация бота
        
        Args:
            bot_token (str): Telegram Bot API токен
            gemini_key (str): Google Gemini API ключ
        """
        self.bot = telebot.TeleBot(bot_token)
        
        # Настройка Gemini
        genai.configure(api_key=gemini_key)
        try:
            # Используем доступные модели из вашего списка
            self.model = genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            print(f"⚠️ Ошибка инициализации gemini-2.0-flash: {e}")
            self.model = genai.GenerativeModel('gemini-flash-latest')
        
        # Хранилище сессий: {user_id: {'history': [], 'last_active': datetime}}
        self.sessions = {}
        self.SESSION_TIMEOUT = timedelta(hours=6)
        
        # Поддержка (Manager)
        self.ADMIN_ID = 5644397480
        self.waiting_for_support = set() # user_ids, ожидающие ввода сообщения для менеджера
        self.waiting_for_search = set()  # user_ids, ожидающие фото для поиска
        self.support_messages = {} # {admin_message_id: user_chat_id} для ответов
        
        # Системный промпт для AI
        self.system_prompt = """
Ты - дружелюбный помощник интернет-магазина "Monvoir" по имени Мона. 
Сайт магазина: https://monvoir.shop
Твоя задача - помогать клиентам с вопросами о товарах.

ПРАВИЛА:
1. Отвечай ТОЛЬКО на основе предоставленной информации о товарах в разделе "ИНФОРМАЦИЯ О ТОВАРАХ".
2. Если информации нет в базе - честно скажи об этом.
3. Будь вежливым, дружелюбным и кратким.
4. Используй HTML теги ТОЛЬКО из этого списка: <b>, <i>, <code>, <s>, <u>, <pre>.
   - <b>жирный текст</b> для названий и цен.
   - <i>курсив</i> для примечаний.
5. ЗАПРЕЩЕНО использовать: <ul>, <ol>, <li>, <p>, <br>, <h1>. 
   - Для списков используй символ "• " с новой строки.
   - Для переноса строк используй обычный перенос строки (Enter).
   - Используй <a href="URL">Текст ссылки</a> для ссылок на товары.
   - Используй <a href="URL">Текст ссылки</a> для ссылок на товары.
6. Не используй Markdown (звездочки, решетки). ТОЛЬКО разрешенный HTML.
7. Не здоровайся в каждом сообщении. Приветствие уместно только в начале диалога.

НАВИГАЦИЯ ПО САЙТУ (Если клиент спрашивает "где кнопка?", "как купить?"):
Сайт имеет верхнюю панель (шапку). Кнопки находятся справа вверху:
• 🛒 **Корзина** (Иконка тележки): Для оформления заказа.
• ❤️ **Избранное** (Иконка сердца): Отложенные товары.
• 👤 **Профиль** (Кнопка "Войти" или иконка человечка): Регистрация и история заказов.
• Логотип (Слева): Возврат на главную страницу в каталог.
• Фильтры: Находятся над списком товаров (Сортировка, Цена).

8. Если клиент спрашивает о наличии - обязательно проверь данные inventory.
9. Цены указывай в сумах c разделителями (например: 150 000 сум).
10. Если клиент хочет купить - предложи связаться с менеджером.
11. Помни контекст беседы. Если клиент спрашивает "А сколько он стоит?", пойми, о каком товаре шла речь ранее.

ПРИМЕР ОТВЕТА (HTML):
У нас есть отличная <a href="https://monvoir.shop/product/123"><b>Футболка Nike</b></a>.

💰 Цена: <b>150 000 сум</b>
🎨 Цвета: Белый, Черный

Хотите оформить заказ?
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
                # Получаем данные о товарах из БД
                products = get_all_products_info()
                
                if not products:
                    self.bot.send_message(
                        message.chat.id,
                        "😔 К сожалению, сейчас в базе данных нет товаров.\n"
                        "Попробуйте позже или свяжитесь с менеджером."
                    )
                    return
                
                # Форматируем данные для AI
                products_context = format_products_for_ai(products)
                
                # Формируем историю
                history_text = self._format_history_for_prompt(session['history'])
                
                # Формируем полный промпт
                full_prompt = f"""{self.system_prompt}

ИНФОРМАЦИЯ О ТОВАРАХ:
{products_context}

{history_text}
КЛИЕНТ: {user_question}

ОТВЕТ (в HTML):"""
                
                # Список доступных моделей (на основе вашего вывода)
                model_names = [
                    'gemini-2.0-flash',       # Новая быстрая версия
                    'gemini-flash-latest',    # Стабильная версия Flash
                    'gemini-pro-latest',      # Стабильная версия Pro
                    'gemini-2.0-flash-lite',  # Облегченная версия
                ]
                response = None
                last_error = None

                for m_name in model_names:
                    try:
                        # print(f"🤖 Попытка использовать модель: {m_name}")
                        model = genai.GenerativeModel(m_name)
                        response = model.generate_content(full_prompt)
                        if response and response.text:
                            # print(f"✅ Успешно использована модель: {m_name}")
                            break
                    except Exception as e:
                        last_error = str(e)
                        # print(f"⚠️ Модель {m_name} не сработала: {e}")
                        continue
                
                if not response:
                    raise Exception(f"Все модели вернули ошибку. Последняя: {last_error}")

                ai_answer = response.text
                
                # Сохраняем в историю
                session['history'].append({'role': 'user', 'text': user_question})
                session['history'].append({'role': 'model', 'text': ai_answer})
                
                # Отправляем ответ клиенту
                try:
                    self.bot.send_message(
                        message.chat.id,
                        ai_answer,
                        parse_mode='HTML'
                    )
                except telebot.apihelper.ApiTelegramException as e:
                    if "can't parse entities" in str(e):
                        # Если HTML сломался, пробуем отправить как текст
                        print(f"⚠️ Ошибка разметки HTML, отправка без форматирования: {e}")
                        self.bot.send_message(
                            message.chat.id,
                            ai_answer, # Отправляем как есть, телеграм сам покажет теги как текст, но сообщение дойдет
                            parse_mode=None
                        )
                    else:
                        raise e
                
            except Exception as e:
                print(f"❌ Ошибка обработки вопроса: {e}")
                self.bot.send_message(
                    message.chat.id,
                    "😔 Извините, произошла техническая ошибка.\n"
                    "Попробуйте переформулировать вопрос."
                )
    
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
