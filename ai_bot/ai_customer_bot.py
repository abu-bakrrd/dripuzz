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
from ai_bot.ai_db_helper import get_all_products_info, search_products, format_products_for_ai, get_order_status, format_colors

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
        
        # Хранилище сессий: {user_id: {'history': [], 'last_active': datetime, 'last_search_offset': int}}
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
Ты — <b>Mona</b>, очаровательная, умная и всегда готовая помочь девушка-ассистент магазина мужской одежды Monvoir (<a href="https://monvoir.shop"><b>monvoir.shop</b></a>).

ТВОЯ РОЛЬ:
- Ты — лицо магазина. Общайся мягко, вежливо и по-женски тепло. 
- Всегда представляйся: "Привет! Я Mona ✨". 
- Используй женские формы глаголов (я нашла, я подготовила, я рада).
- Для вывода товаров используй тег: <code>[ТОВАРЫ:старт,стоп]</code>.

КРИТИЧЕСКИЕ ПРАВИЛА:
1. <b>ССЫЛКИ</b>: Ссылку на сайт ВСЕГДА делай жирной: <a href="https://monvoir.shop"><b>monvoir.shop</b></a>.
2. <b>НИКОГДА</b> не пиши списки товаров сама. Только тег <code>[ТОВАРЫ:a,b]</code>.
3. <b>ПРИВЕТСТВИЕ</b>: Сначала теплое приветствие и знакомство, потом всё остальное.
4. <b>ЛОГИКА</b>: Твой текст должен обволакивать список товаров. Сначала превью, потом тег, потом нежное завершение.
5. <b>СТИЛЬ</b>: Используй много "женских" и уютных эмодзи: ✨, 💖, 💕, 🌸, 👔, 🛍️, ✅.

ИНФОРМАЦИЯ О ТОВАРАХ (ТОВАРЫ В МАГАЗИНЕ):
Я буду присылать тебе список названий найденных товаров, чтобы ты понимала ассортимент, но НЕ ДУБЛИРУЙ их названия в тексте, их выведет функция.
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
                self.sessions[user_id] = {
                    'history': [], 
                    'last_active': now,
                    'last_products': [],
                    'current_offset': 0
                }
                return self.sessions[user_id]
            
            # Обновляем время активности
            session['last_active'] = now
            return session
        
        # Новая сессия
        self.sessions[user_id] = {
            'history': [], 
            'last_active': now,
            'last_products': [],
            'current_offset': 0
        }
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
    
    def _get_formatted_products(self, products, offset=0, limit=4):
        """
        Возвращает отформатированную строку со списком товаров
        
        Args:
            products (list): Полный список найденных товаров
            offset (int): Начальный индекс
            limit (int): Количество товаров для отображения
            
        Returns:
            str: Отформатированный текст или пустая строка
        """
        if not products:
            return False
            
        current_batch = products[offset:offset + limit]
        if not current_batch:
            return False
            
        text = "👔💼 <b>Вот несколько товаров в наличии! ✨</b>\n\n"
        
        for idx, product in enumerate(current_batch, offset + 1):
            product_url = f"https://monvoir.shop/product/{product['id']}"
            price_formatted = f"{product['price']:,} сум"
            
            text += f"{idx}. <a href=\"{product_url}\"><b>{product['name']}</b></a> - <b>{price_formatted}</b> ✅ В наличии"
            
            # Добавляем краткую информацию о наличии (цвета/размеры)
            inventory = product.get('inventory', [])
            if inventory:
                available_variants = [item for item in inventory if item['quantity'] > 0]
                if available_variants:
                    variants_parts = []
                    # Берем первые 2 уникальных варианта для краткости
                    seen_variants = set()
                    for item in available_variants:
                        parts = []
                        if item.get('color'):
                            parts.append(format_colors([item['color']]))
                        if item.get('attribute1_value'):
                            parts.append(item['attribute1_value'])
                        
                        variant_str = ", ".join(parts)
                        if variant_str and variant_str not in seen_variants:
                            variants_parts.append(variant_str)
                            seen_variants.add(variant_str)
                            if len(variants_parts) >= 2: break
                    
                    if variants_parts:
                        text += f": {'; '.join(variants_parts)}"
            
            text += "\n\n"
            
        # Подвал
        text += "🛍️ Вы можете посетить наш <a href=\"https://monvoir.shop/\"><b>полный каталог</b></a> на сайте."
        
        return text

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
            
            user_question = message.text or ""
            clean_question = user_question.lower().strip()
            
            # 1. Проверка на приветствие (чтобы не дергать БД лишний раз и не путать Мону)
            greetings = ['привет', 'здравствуй', 'добрый день', 'добрый вечер', 'доброе утро', 'хай', 'hi', 'hello']
            is_simple_greeting = any(word == clean_question for word in greetings) or clean_question == "start"
            
            # 2. Проверка: Ждем ли мы сообщение для менеджера или поиска?
            if user_id in self.waiting_for_support or user_id in self.waiting_for_search:
                self._forward_to_admin(message, "Поиск по фото" if user_id in self.waiting_for_search else "Запрос менеджера")
                return

            # Проверка наличия ID заказа в сообщении
            potential_ids = []
            potential_ids.extend(re.findall(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', clean_question))
            potential_ids.extend(re.findall(r'\b[0-9a-f]{6,}\b', clean_question))
            
            if potential_ids:
                for oid in potential_ids:
                    short_info = get_order_status(oid, detailed=False)
                    if short_info and "Заказ #" in short_info:
                        self.bot.send_message(message.chat.id, short_info, parse_mode='HTML')
                        found_order_full = get_order_status(oid, detailed=True)
                        self._update_history(user_id, user_question, found_order_full)
                        return
            
            # Получаем сессию
            session = self._get_user_session(user_id)
            products_text = None  
            
            self.bot.send_chat_action(message.chat.id, 'typing')
            
            try:
                # 3. Подготовка контекста товаров
                products_context = ""
                found_products_list = []
                
                # Если это НЕ просто приветствие - ищем товары
                if not is_simple_greeting:
                    # Проверяем, просит ли пользователь "еще"
                    more_keywords = ['еще', 'другие', 'покажи еще', 'еще товары', 'больше', 'дальше', 'next']
                    is_more_request = any(keyword in clean_question for keyword in more_keywords)
                    
                    if is_more_request and session.get('last_products'):
                        # Берем предыдущий поиск
                        found_products_list = session['last_products']
                    else:
                        # Новый поиск
                        # Определяем, общий ли это запрос
                        general_questions = ['какие товары', 'что есть', 'что у вас', 'ассортимент', 'в наличии', 'каталог']
                        is_general = any(phrase in clean_question for phrase in general_questions)
                        
                        if is_general:
                            found_products_list = get_all_products_info()
                        else:
                            found_products_list = search_products(user_question)
                        
                        session['last_products'] = found_products_list

                    if found_products_list:
                        count = len(found_products_list)
                        names = ", ".join([p['name'] for p in found_products_list[:15]]) # Только имена для контекста
                        products_context = f"ТОВАРЫ В МАГАЗИНЕ:\nНайдено всего: {count} шт.\nСписок (кратко): {names}\nЧтобы показать товары, используй [ТОВАРЫ:старт,стоп]."
                        if is_more_request:
                            current = session.get('current_offset', 0)
                            products_context += f"\nПользователь просит ЕЩЕ. Ты уже показала товары до индекса {current}. Используй [{current},{current+10}]."
                    else:
                        products_context = "ТОВАРЫ В МАГАЗИНЕ:\nВ наличии ничего не найдено по этому запросу. Предложи заглянуть на сайт или спросить по-другому."

                # Генерируем ответ AI
                if self.client:
                    sys_msg = f"{self.system_prompt}\n\nКОНТЕКСТ:\n{products_context}"
                    if is_simple_greeting:
                        sys_msg += "\n\nВНИМАНИЕ: Это просто приветствие. Будь дружелюбна, НЕ используй тег товаров."

                    messages = [{"role": "system", "content": sys_msg}]
                    
                    # История
                    for msg in session['history'][-6:]:
                        messages.append({"role": "user" if msg['role'] == "user" else "assistant", "content": msg['text']})
                    
                    messages.append({"role": "user", "content": user_question})

                    completion = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=800
                    )
                    
                    response_text = self._clean_thinking_tags(completion.choices[0].message.content)
                    
                    # 4. Обработка тега [ТОВАРЫ:a,b]
                    final_response = response_text
                    tag_match = re.search(r'\[ТОВАРЫ:(\d+),(\d+)\]', response_text)
                    
                    if tag_match and found_products_list:
                        start = int(tag_match.group(1))
                        end = int(tag_match.group(2))
                        session['current_offset'] = end
                        
                        # Вызываем "красивую функцию"
                        pretty_list = self._get_formatted_products(found_products_list, start, end - start)
                        
                        if pretty_list:
                            final_response = response_text.replace(tag_match.group(0), f"\n\n{pretty_list}")
                        else:
                            final_response = response_text.replace(tag_match.group(0), "\n\n(К сожалению, больше товаров в этом списке нет) ✨")
                    
                    # Финальная отправка
                    try:
                        self.bot.send_message(message.chat.id, final_response, parse_mode='HTML', disable_web_page_preview=True)
                    except Exception:
                        self.bot.send_message(message.chat.id, final_response)
                        
                    self._update_history(user_id, user_question, final_response)
                else:
                    self.bot.send_message(message.chat.id, "Mona сейчас отдыхает, попробуйте позже! ✨")
            except Exception as e:
                print(f"❌ Error in handle_question: {e}")
                self.bot.send_message(message.chat.id, "Произошла небольшая заминка, я уже исправляюсь! ✨")

    
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
