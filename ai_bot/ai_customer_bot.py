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
                # Используем модель llama-4-scout для инструкций
                self.model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
                print(f"✅ Модель: Groq {self.model_name} подключена", flush=True)
            except Exception as e:
                print(f"⚠️ Ошибка инициализации Groq: {e}", flush=True)
                self.client = None
        
        # Хранилище сессий: {user_id: {'history': [], 'last_active': datetime}}
        self.sessions = {}
        self.SESSION_TIMEOUT = timedelta(hours=6)
        
        # Кеш частых запросов: {normalized_query: {'response': str, 'expires': datetime}}
        self.response_cache = {}
        self.CACHE_TTL = timedelta(hours=1)
        
        # Поддержка (Manager)
        self.ADMIN_ID = 5644397480
        self.waiting_for_support = set()
        self.waiting_for_search = set()
        self.support_messages = {}
        
        # Защита от спама: {user_id: {'count': int, 'last_message': datetime}}
        self.spam_protection = {}
        self.SPAM_LIMIT = 10  # Максимум сообщений
        self.SPAM_WINDOW = timedelta(minutes=1)  # За 1 минуту
        
        # Системный промпт для AI (оптимизирован)
        self.system_prompt = """
Ты — <b>Mona</b>, AI-консультант магазина мужской одежды "Monvoir" (<a href="https://monvoir.shop">сайт</a>).

ЛИЧНОСТЬ: Профессиональная, вежливая, объективная. Используй эмодзи умеренно (✨, 👔, 💼, 📦, ✅, 🔍).

ПРАВИЛА ОБЩЕНИЯ:
- Отвечай ТОЛЬКО на заданные вопросы, без лишнего. Будь лаконичной.
- НЕ предлагай товары/команды/дополнительную информацию без запроса.
- НЕ задавай встречных вопросов, если клиент их не задал.
- Команды предлагай ТОЛЬКО в крайних случаях (возвраты, скидки → /manager; товара нет в каталоге → /search).

КОМАНДЫ: /start (меню), /search (поиск по фото, ТОЛЬКО если товара нет в каталоге), /manager (живой менеджер для возвратов/скидок), /help (справка). Предлагай команды ТОЛЬКО если клиент спрашивает или в крайних случаях.

ОПЕРАЦИИ: Можешь называть цены. НЕ можешь делать возвраты/скидки → предложи /manager.

НАВИГАЦИЯ: Главная (каталог, фильтры), Карточка товара (выбор цвета/размера, "Добавить в корзину"), Корзина (оформление), Избранное, Профиль (заказы). Ссылки: <a href="https://monvoir.shop">сайт</a>, <a href="https://monvoir.shop/cart">корзина</a>.

ЗАКАЗ: 1) Выбор товара → 2) Карточка (цвет/размер) → 3) "Добавить в корзину" → 4) Корзина → 5) "Оформить заказ" → 6) Данные (имя, телефон, адрес, оплата) → 7) Подтверждение → 8) Отслеживание в "Заказы". Оплата: Click, Payme, Uzum Bank, перевод на карту. Доставка оплачивается при получении.

ФОРМАТИРОВАНИЕ: ТОЛЬКО HTML (не Markdown). Ссылки: <a href="url"><b>текст</b></a>, НИКОГДА не показывай открытые URL. Используй <b> для цен/названий, <i> для описаний. Эмодзи: ✨, 👔, 💼, 📦, ✅, 🔍. Цвета: названия на русском (не HEX). ТОЧНОСТЬ: используй точные названия из базы, не выдумывай. Без thinking tags.
"""
        
        # Регистрация обработчиков
        self._register_handlers()
        
        # Очистка старых сессий при старте
        self._cleanup_sessions()
    
    def _cleanup_sessions(self):
        """Очищает неактивные сессии и устаревший кеш"""
        now = datetime.now()
        
        # Очистка сессий
        expired_users = []
        for user_id, session in self.sessions.items():
            if now - session['last_active'] > self.SESSION_TIMEOUT:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            del self.sessions[user_id]
        
        # Очистка кеша ответов
        expired_cache_keys = []
        for key, cached in self.response_cache.items():
            if now >= cached['expires']:
                expired_cache_keys.append(key)
        
        for key in expired_cache_keys:
            del self.response_cache[key]
        
        if expired_users or expired_cache_keys:
            print(f"🧹 Очищено: {len(expired_users)} сессий, {len(expired_cache_keys)} записей кеша", flush=True)
    
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
        """Форматирует историю переписки для AI с ограничением длины"""
        if not history:
            return ""
        
        # Берем последние 6 сообщений и ограничиваем общую длину
        MAX_HISTORY_LENGTH = 2000
        recent_messages = history[-6:]  # Уменьшено с 10 до 6
        
        conversation_text = "\nИСТОРИЯ ПЕРЕПИСКИ:\n"
        total_length = len(conversation_text)
        
        for msg in reversed(recent_messages):  # Идем с конца
            role = "КЛИЕНТ" if msg['role'] == 'user' else "ТЫ (БОТ)"
            msg_text = msg['text']
            
            # Обрезаем слишком длинные сообщения
            if len(msg_text) > 300:
                msg_text = msg_text[:300] + "..."
            
            line = f"{role}: {msg_text}\n"
            
            # Проверяем, не превысим ли лимит
            if total_length + len(line) > MAX_HISTORY_LENGTH:
                break
                
            conversation_text = line + conversation_text
            total_length += len(line)
        
        return conversation_text
    
    def _check_spam(self, user_id):
        """
        Проверяет, не превышен ли лимит сообщений от пользователя (защита от спама)
        
        Args:
            user_id (int): ID пользователя
            
        Returns:
            bool: True если это спам, False если нормально
        """
        now = datetime.now()
        
        if user_id not in self.spam_protection:
            self.spam_protection[user_id] = {
                'count': 1,
                'last_message': now
            }
            return False
        
        user_data = self.spam_protection[user_id]
        
        # Если прошло больше времени окна - сбрасываем счетчик
        if now - user_data['last_message'] > self.SPAM_WINDOW:
            user_data['count'] = 1
            user_data['last_message'] = now
            return False
        
        # Увеличиваем счетчик
        user_data['count'] += 1
        user_data['last_message'] = now
        
        # Проверяем лимит
        if user_data['count'] > self.SPAM_LIMIT:
            return True
        
        return False
    
    def _normalize_query(self, query):
        """Нормализует запрос для кеширования"""
        # Приводим к нижнему регистру, убираем лишние пробелы
        normalized = query.lower().strip()
        # Убираем знаки препинания для лучшего совпадения
        normalized = re.sub(r'[^\w\s]', '', normalized)
        # Убираем множественные пробелы
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized
    
    def _get_cached_response(self, query):
        """Проверяет кеш для частых запросов"""
        normalized = self._normalize_query(query)
        now = datetime.now()
        
        # Частые вопросы для кеширования
        frequent_queries = {
            'как заказать': 'как заказать',
            'как купить': 'как заказать',
            'как оформить заказ': 'как заказать',
            'способы оплаты': 'способы оплаты',
            'как оплатить': 'способы оплаты',
            'доставка': 'доставка',
            'как доставляют': 'доставка',
            'навигация': 'навигация',
            'как пользоваться сайтом': 'навигация',
        }
        
        # Проверяем, является ли это частым вопросом
        cache_key = None
        for pattern, key in frequent_queries.items():
            if pattern in normalized:
                cache_key = key
                break
        
        if cache_key and cache_key in self.response_cache:
            cached = self.response_cache[cache_key]
            if now < cached['expires']:
                return cached['response']
            else:
                # Удаляем устаревший кеш
                del self.response_cache[cache_key]
        
        return None
    
    def _cache_response(self, query, response):
        """Сохраняет ответ в кеш"""
        normalized = self._normalize_query(query)
        
        # Частые вопросы для кеширования
        frequent_queries = {
            'как заказать': 'как заказать',
            'как купить': 'как заказать',
            'как оформить заказ': 'как заказать',
            'способы оплаты': 'способы оплаты',
            'как оплатить': 'способы оплаты',
            'доставка': 'доставка',
            'как доставляют': 'доставка',
            'навигация': 'навигация',
            'как пользоваться сайтом': 'навигация',
        }
        
        cache_key = None
        for pattern, key in frequent_queries.items():
            if pattern in normalized:
                cache_key = key
                break
        
        if cache_key:
            self.response_cache[cache_key] = {
                'response': response,
                'expires': datetime.now() + self.CACHE_TTL
            }
    
    def _clean_thinking_tags(self, text):
        """
        Удаляет thinking tags и подобные конструкции из ответа AI
        
        Args:
            text (str): Текст ответа от AI
            
        Returns:
            str: Очищенный текст
        """
        # re уже импортирован глобально
        
        # Удаляем различные варианты thinking tags
        patterns = [
            r'<think>.*?</think>',  # <think>...</think>
            r'\[think\].*?\[/think\]',  # [think]...[/think]
            r'\(think:.*?\)',  # (think:...)
            r'<thinking>.*?</thinking>',  # <thinking>...</thinking>
            r'\[thinking\].*?\[/thinking\]',  # [thinking]...[/thinking]
            r'<reasoning>.*?</reasoning>',  # <reasoning>...</reasoning>
            r'<internal>.*?</internal>',  # <internal>...</internal>
            r'```thinking.*?```',  # ```thinking...```
            r'```reasoning.*?```',  # ```reasoning...```
        ]
        
        cleaned_text = text
        for pattern in patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Удаляем множественные пустые строки
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        # Убираем пробелы в начале и конце
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text

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
👋 Привет, <b>{username}</b>! 💕

Меня зовут <b>Mona</b>, и я твой AI-консультант магазина Monvoir! ✨

Я помогу тебе найти идеальные вещи и ответить на любые вопросы:

• Какие товары есть в наличии? 👔
• Какие цвета и размеры доступны? 🎨
• Сколько стоит товар? 💰
• Что есть в конкретной категории? 📂
• /search - поиск по фото 📸
• /manager - позвать живого менеджера 👨‍💼

Просто напиши мне свой вопрос, и я с радостью помогу! 💖
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
            
            # Защита от спама
            if self._check_spam(user_id):
                self.bot.send_message(
                    message.chat.id,
                    "⏳ Пожалуйста, подождите немного перед следующим сообщением. Слишком много запросов за короткое время."
                )
                return
            
            user_question = message.text
            
            # 1. Проверка: Ждем ли мы сообщение для менеджера или поиска?
            if user_id in self.waiting_for_support or user_id in self.waiting_for_search:
                self._forward_to_admin(message, "Поиск по фото" if user_id in self.waiting_for_search else "Запрос менеджера")
                return

            # Проверка наличия ID заказа в сообщении
            # Ищем UUID или короткий ID (6+ символов, hex)
            clean_text = user_question.lower()
            potential_ids = []
            
            # 1. UUID Pattern
            potential_ids.extend(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', clean_text))
            # 2. Short ID Pattern (6+ hex chars)
            potential_ids.extend(re.findall(r'\b[0-9a-f]{6,}\b', clean_text))
            
            # Проверяем кандидатов в базе данных
            found_order_full = None
            found_order_short = None
            
            for oid in potential_ids:
                # Игнорируем слишком длинные последовательности, если это не UUID
                # Пробуем получить короткую версию для отправки пользователю
                short_info = get_order_status(oid, detailed=False)
                
                # Проверяем, что вернулся успешный ответ
                if short_info and "Заказ #" in short_info:
                    found_order_short = short_info
                    # Получаем полную версию для истории
                    found_order_full = get_order_status(oid, detailed=True)
                    break
            
            if found_order_short:
                self.bot.send_message(message.chat.id, found_order_short, parse_mode='HTML')
                # ВАЖНО: сохраняем ПОЛНЫЙ ответ базы данных в историю, чтобы AI знал детали
                self._update_history(user_id, user_question, found_order_full)
                return
            
            # Получаем сессию
            session = self._get_user_session(user_id)
            
            # Отправляем индикатор "печатает..."
            self.bot.send_chat_action(message.chat.id, 'typing')
            
            try:
                # 2. Получаем контекст товаров - ВСЕГДА используем поиск
                products_context = "Информацию о товарах пока получить не удалось."
                found_products_list = []  # Для проверки наличия товаров
                is_search_query = False  # Флаг: был ли это поиск конкретного товара
                try:
                    # Определяем, является ли запрос общим вопросом
                    general_questions = ['какие товары', 'что есть', 'что у вас', 'покажи все', 'какой ассортимент', 'что продаете', 'что в наличии']
                    is_general = any(phrase in user_question.lower() for phrase in general_questions)
                    
                    # ВСЕГДА используем поиск, даже для общих вопросов
                    found_products_list = search_products(user_question)
                    
                    if found_products_list:
                        # Ограничиваем до 3-5 товаров максимум
                        is_search_query = True
                        products_context = format_products_for_ai(found_products_list[:3])
                    elif is_general:
                        # Если общий вопрос и ничего не найдено - показываем несколько примеров
                        all_products = get_all_products_info()
                        found_products_list = all_products[:3] if all_products else []
                        products_context = format_products_for_ai(found_products_list) if found_products_list else "ТОВАРЫ В МАГАЗИНЕ:\n\nВ каталоге пока нет товаров."
                    else:
                        # Конкретный запрос, но ничего не найдено
                        products_context = "ТОВАРЫ В МАГАЗИНЕ:\n\nТовар не найден в каталоге."
                except Exception as e:
                    print(f"⚠️ Ошибка получения товаров: {e}")

                # 3. Проверка на статус заказа (уже проверено выше, но если не найден - добавляем в контекст для AI)
                order_info = ""
                # Заказ уже проверен выше (строки 456-486), если он был найден - мы уже вернулись
                # Здесь проверяем только если заказ не был найден в первой проверке, но пользователь может спрашивать о нем
                
                # Проверяем кеш перед запросом к AI
                cached_response = self._get_cached_response(user_question)
                if cached_response:
                    self.bot.send_message(
                        message.chat.id,
                        cached_response,
                        parse_mode='HTML'
                    )
                    # Сохраняем в историю
                    self._update_history(user_id, user_question, cached_response)
                    return
                
                # Генерируем ответ
                try:
                    if self.client:
                        # Подготовка сообщений для Groq
                        # Добавляем информацию о том, найден ли товар
                        product_found_note = ""
                        if found_products_list:
                            product_found_note = "\n\nВАЖНО: Товары найдены в каталоге. Покажи их клиенту, НЕ предлагай /search."
                        else:
                            # Проверяем, был ли это поиск конкретного товара
                            if is_search_query:
                                product_found_note = "\n\nВАЖНО: Товар НЕ найден в каталоге. Можешь предложить /search, но только если клиент спрашивал о конкретном товаре, которого нет в магазине."
                        
                        messages = [
                            {"role": "system", "content": f"{self.system_prompt}\n\nИНФОРМАЦИЯ О ТОВАРАХ:\n{products_context}{product_found_note}\n\n{order_info if order_info else ''}"}
                        ]
                        
                        # Добавляем историю переписки (оптимизировано: максимум 6 сообщений, 2000 символов)
                        MAX_HISTORY_TOKENS = 2000
                        total_length = 0
                        history_messages = []
                        
                        for msg in reversed(session['history'][-6:]):  # Последние 6 сообщений
                            role = "user" if msg['role'] == "user" else "assistant"
                            content = msg['text']
                            
                            # Обрезаем слишком длинные сообщения
                            if len(content) > 300:
                                content = content[:300] + "..."
                            
                            if total_length + len(content) > MAX_HISTORY_TOKENS:
                                break
                                
                            history_messages.insert(0, {"role": role, "content": content})
                            total_length += len(content)
                        
                        messages.extend(history_messages)
                        
                        # Добавляем текущий вопрос
                        messages.append({"role": "user", "content": user_question})

                        # Вызов API
                        try:
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
                        except Exception as api_error:
                            # Обработка ошибок API
                            error_str = str(api_error)
                            error_lower = error_str.lower()
                            
                            # Обработка ошибки 429 (Rate Limit)
                            if '429' in error_str or 'rate limit' in error_lower or 'rate_limit' in error_lower:
                                # Пытаемся извлечь время ожидания из ошибки
                                # re уже импортирован глобально
                                retry_after_match = re.search(r'retry[_-]?after[:\s]+(\d+)', error_str, re.IGNORECASE)
                                if retry_after_match:
                                    seconds = int(retry_after_match.group(1))
                                    minutes = (seconds + 59) // 60  # Округляем вверх
                                    wait_time = f"{minutes} минут" if minutes > 0 else f"{seconds} секунд"
                                else:
                                    # Если не нашли точное время, используем дефолтное
                                    wait_time = "1-2 минуты"
                                
                                self.bot.send_message(
                                    message.chat.id,
                                    f"⏳ <b>Слишком много запросов</b>\n\n"
                                    f"Пожалуйста, подождите <b>{wait_time}</b> перед следующим сообщением.\n\n"
                                    f"<i>Система временно ограничила количество запросов для обеспечения стабильной работы.</i>",
                                    parse_mode='HTML'
                                )
                                return
                            # Обработка ошибки модели (404, model not found и т.д.)
                            elif '404' in error_str or 'not found' in error_lower or 'model' in error_lower and ('invalid' in error_lower or 'unknown' in error_lower):
                                print(f"❌ Ошибка модели: {api_error}", flush=True)
                                self.bot.send_message(
                                    message.chat.id,
                                    "⚠️ <b>Ошибка AI модели</b>\n\n"
                                    "К сожалению, сейчас AI недоступен. Пожалуйста, попробуйте позже или используйте команду /manager для связи с менеджером.",
                                    parse_mode='HTML'
                                )
                                return
                            else:
                                # Другие ошибки API - логируем и сообщаем пользователю
                                print(f"❌ Ошибка API: {api_error}", flush=True)
                                self.bot.send_message(
                                    message.chat.id,
                                    "⚠️ <b>Временная ошибка</b>\n\n"
                                    "Произошла ошибка при обработке запроса. Пожалуйста, попробуйте позже или используйте команду /manager.",
                                    parse_mode='HTML'
                                )
                                return
                         
                        if response_text:
                             # Очищаем thinking tags и подобные конструкции
                             response_text = self._clean_thinking_tags(response_text)
                             
                             # Кешируем ответ для частых вопросов
                             self._cache_response(user_question, response_text)
                             
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
        print("🤖 AI Customer Bot запущен и готов к работе (v3.2 STABLE)...")
        print(f"✅ Модель: {self.model_name if self.client else 'Не подключена'}")
        print("✅ Память: включена (тайм-аут 6 часов)")
        print(f"📊 Бот: @{self.bot.get_me().username}")
        print("👩 Mona готова помогать клиентам! 💕")
        
        # Запускаем периодическую очистку сессий в отдельном потоке
        import threading
        def cleanup_loop():
            import time
            while True:
                time.sleep(3600)  # Каждый час
                self._cleanup_sessions()
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        
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
