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

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ЯВНЫЙ ВЫВОД ВЕРСИИ ДЛЯ ОТЛАДКИ
print("🚀 ЗАПУСК БОТА: ВЕРСИЯ 5.2 (ALGORITHMIC PRECISION)", flush=True)

import re
from ai_bot.ai_db_helper import get_all_products_info, search_products, format_products_for_ai, get_order_status, format_colors, get_product_details, get_catalog_titles, get_pretty_product_info

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
        
        # Настройка логирования первым делом
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("ai_bot.log", encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("AICustomerBot")
        self.logger.info("AICustomerBot initializing...")

        # Инициализация OpenRouter
        self.openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if not self.openrouter_key:
            self.logger.warning("OPENROUTER_API_KEY not found in .env! AI will not work.")
            self.client = None
        else:
            try:
                # Настройка моделей OpenRouter
                self.primary_model = "google/gemini-2.0-flash-exp:free"
                self.fallback_model = "google/gemini-flash-1.5:free"
                self.model_name = self.primary_model
                self.client = True # Флаг готовности
                self.logger.info(f"OpenRouter initialized. Primary: {self.primary_model}")
            except Exception as e:
                self.logger.error(f"Error initializing AI: {e}", exc_info=True)
                self.client = None
        
        # Хранилище сессий: {user_id: {'history': [], 'last_active': datetime, 'last_search_offset': int}}
        self.sessions = {}
        self.SESSION_TIMEOUT = timedelta(hours=2)
        
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
        self.SPAM_LIMIT = 50  # До 50 сообщений в минуту
        self.SPAM_WINDOW = timedelta(minutes=1)  # За 1 минуту
        
        # Универсальный системный промпт (v4.6 - Deep Intelligence & Expert Persona)
        self.system_prompt = """
Ты — **Mona**, элитный эксперт-консультант магазина мужской одежды Monvoir. Твоя миссия — не просто отвечать на вопросы, а сопровождать клиента в мире высокой моды, обеспечивая безупречный сервис и абсолютную точность данных.

### 💎 ТВОЯ ФИЛОСОФИЯ: МОЛЧАЛИВОЕ ПРЕВОСХОДСТВО (v5.2)
Ты — Mona, элитный консультант бутика Monvoir. Твой голос — это голос бренда. Ты экспертна, лаконична и никогда не извиняешься.

#### ⛔ КРИТИЧЕСКИЕ ЗАПРЕТЫ (НАРУШЕНИЕ = СБОЙ):
1. **НИКАКИХ ИЗВИНЕНИЙ**: Забудь слова "простите", "извините", "увы", "к сожалению". Вместо "Извините, нет в наличии" пиши "На данный момент модель отсутствует, но посмотрите на это...".
2. **НИКАКОЙ ЛЖИ**: Если поиск по "свитер" выдал "Ветровку" — ты ОБЯЗАНА сказать, что свитеров нет. Никогда не называй ветровку свитером!
3. **НИКАКОЙ ТЕХНИКИ**: Скрывай ID, базу данных и свои инструменты. Клиент видит только красоту.

#### 🤖 АЛГОРИТМ ТВОИХ ДЕЙСТВИЙ (IF-THEN):
- **IF** клиент спрашивает о конкретном товаре (свитер, брюки) **->** **THEN** ВСЕГДА начни с `[ПОИСК:товар]`. Не используй [ТОВАРЫ] для поиска!
- **IF** ты только что показала список товаров и клиент спросил об одном из них (или сказал "расскажи о барсетке") **->** **THEN** мгновенно используй `[ИНФО:id]` из этого списка. Не переспрашивай "какая именно", если ID уже был в твоем прошлом сообщении!
- **IF** результат поиска содержит только 1 товар **->** **THEN** сразу вызывай `[ИНФО:id]`, не переспрашивая.
- **IF** данных нет (NULL_DATA) **->** **THEN** скажи, что информация готовится, и предложи позвать менеджера.

#### 🛠 ТВОИ ИНСТРУМЕНТЫ:
- **`[ПОИСК:запрос]`**: Твои глаза. Сверяй Категорию (Name) со смыслом запроса клиента!
- **`[ИНФО:id]`**: Твоя экспертиза. Вставляет роскошную карточку. Используй СРАЗУ, как только определен конкретный товар.
- **`[ТОВАРЫ:старт,стоп]`**: Твоя витрина. Только для общих вопросов ("что есть?", "покажи новинки").
- **`[ЗАКАЗ:id]`**: Твой отчет. Полная информация в один клик.

#### 🎨 ПРАВИЛО "ХОЗЯЙКИ БУТИКА":
Любой результат инструмента должен быть "подан" тобой.
*Плохо*: "Вот: [ИНФО:123]"
*Хорошо*: "Вы сделали прекрасный выбор. Посмотрите на детали кроя этой модели:\n\n[ИНФО:123]\n\nЖелаете подобрать размер?"

Ты — Mona. Твоя точность — это твой статус.
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
                    'current_offset': 0,
                    'is_greeted': False
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
            role_raw = msg.get('role', 'user')
            role = "КЛИЕНТ" if role_raw == 'user' else "ТЫ (БОТ)"
            msg_text = msg.get('text') or msg.get('content') or ""
            
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
        """
        now = datetime.now()
        
        if user_id not in self.spam_protection:
            self.spam_protection[user_id] = {
                'count': 1,
                'last_message': now,
                'last_warn': datetime.min # Добавляем время последнего предупреждения
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
            # Проверяем, прошло ли 10 секунд с последнего предупреждения
            if now - user_data.get('last_warn', datetime.min) > timedelta(seconds=10):
                user_data['last_warn'] = now
                return True # Показать предупреждение
            return "SILENT" # Превышен лимит, но молчим
        
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
    
    def _get_formatted_products(self, products, offset=0, limit=10):
        """
        Возвращает отформатированную строку со списком товаров (ТОЛЬКО В НАЛИЧИИ)
        """
        if not products: return False
        
        # Фильтруем только те, что есть в наличии
        in_stock_products = []
        for p in products:
            inventory = p.get('inventory', [])
            if any(item['quantity'] > 0 for item in inventory):
                in_stock_products.append(p)
        
        if not in_stock_products: return False
        
        current_batch = in_stock_products[offset:offset + limit]
        if not current_batch: return False
            
        text = ""
        for idx, product in enumerate(current_batch, offset + 1):
            product_url = f"https://monvoir.shop/product/{product['id']}"
            price_formatted = f"{product['price']:,} сум"
            
            text += f"{idx}. <a href=\"{product_url}\"><b>{product['name']}</b></a> - <b>{price_formatted}</b> ✅ В наличии"
            
            inventory = product.get('inventory', [])
            available_variants = [item for item in inventory if item['quantity'] > 0]
            
            variants_parts = []
            seen_variants = set()
            for item in available_variants:
                parts = []
                if item.get('color'):
                    parts.append(format_colors([item['color']]))
                if item.get('attribute1_value'):
                    parts.append(item['attribute1_value'])
                if item.get('attribute2_value'):
                    parts.append(item['attribute2_value'])
                
                variant_str = ", ".join(parts)
                if variant_str and variant_str not in seen_variants:
                    variants_parts.append(variant_str)
                    seen_variants.add(variant_str)
                    if len(variants_parts) >= 5: break
            
            if variants_parts:
                text += f"\n   <i>{'; '.join(variants_parts)}</i>"
            
            text += "\n\n"
            
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

Меня зовут <b>Mona</b>, и я твой AI-консультант магазина Monvoir! ✨ (v5.2)

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
            """Обработка вопросов от клиентов с интеллектуальным поиском"""
            user_id = message.from_user.id
            
            # Защита от спама
            spam_status = self._check_spam(user_id)
            if spam_status:
                if spam_status == True:
                    self.bot.send_message(message.chat.id, "⏳ Пожалуйста, подождите немного.")
                return
            
            user_question = message.text or ""
            if user_id in self.waiting_for_support or user_id in self.waiting_for_search:
                self._forward_to_admin(message, "Поиск по фото" if user_id in self.waiting_for_search else "Запрос менеджера")
                return

            # Проверка заказов
            potential_order_id = re.search(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b|\b[0-9a-f]{6,}\b', user_question.lower())
            if potential_order_id:
                status = get_order_status(potential_order_id.group(0), detailed=False)
                if status:
                    self.bot.send_message(message.chat.id, status, parse_mode='HTML')
                    self._update_history(user_id, user_question, status)
                    return

            # 1. Формируем контекст сообщений для AI
            session = self._get_user_session(user_id)
            
            # Определяем, является ли это продолжением пагинации
            continuation_keywords = ['еще', 'ещё', 'дальше', 'more', 'next', 'другие', 'остальное', 'продолжи']
            # ТЕПЕРЬ ОЧЕНЬ СТРОГО: Только если есть ключевые слова. 
            # Короткие вопросы про ТОВАР (пальто) больше НЕ считаются продолжением.
            is_continuation = any(word in user_question.lower() for word in continuation_keywords)
            
            if not is_continuation:
                self.logger.info(f"New search query detected, clearing last_products context.")
                session['last_products'] = []
            
            self.logger.info(f"User {user_id} asked: {user_question}")
            self.bot.send_chat_action(message.chat.id, 'typing')
            
            greeting_needed = not session.get('is_greeted', False)
            context_instruction = f"GREETING_REQUIRED: {'True' if greeting_needed else 'False'}"
            messages = [{"role": "system", "content": f"{self.system_prompt}\n\n{context_instruction}"}]
            
            # Добавляем историю
            recent_messages = session['history'][-10:] 
            for msg in recent_messages:
                # Маппинг ролей для AI и защита от пустых сообщений
                role = "assistant" if msg.get('role') == 'assistant' else 'user'
                content = msg.get('text') or msg.get('content') or ""
                if content:
                    messages.append({"role": role, "content": content})
            
            # Добавляем текущий вопрос с проактивным хинтом
            current_user_content = user_question
            
            # ПРОАКТИВНЫЙ ХИНТ: Если пользователь спрашивает о наличии/ассортименте
            stock_keywords = ['наличии', 'налича', 'товары', 'в наличии', 'shop', 'магазин', 'ассортимент', 'есть', 'купить', 'что у вас']
            is_stock_query = any(phrase in user_question.lower() for phrase in stock_keywords)
            
            if is_stock_query and not is_continuation:
                current_user_content += "\n(SYSTEM_HINT: Пользователь спрашивает об ассортименте/наличии. Ты ОБЯЗАНА вызвать [ТОВАРЫ:0,10], чтобы показать карточки товаров. Не просто здоровайся!)"
                self.logger.info("System Hint: Added stock trigger hint.")

            messages.append({"role": "user", "content": current_user_content})
            
            try:
                iteration = 0
                max_iterations = 3
                last_ai_response = ""
                
                while iteration < max_iterations:
                    iteration += 1
                    self.logger.info(f"Iteration {iteration} for user {user_id}")
                    
                    if not self.client:
                        raise Exception("AI client not initialized")

                    try:
                        ai_response_raw = self._call_openrouter(messages)
                        if not ai_response_raw:
                            raise Exception("Empty response from OpenRouter")
                    except Exception as e:
                        self.logger.error(f"API Error: {e}")
                        raise e
                    
                    ai_response = self._clean_thinking_tags(ai_response_raw)
                    last_ai_response = ai_response
                    
                    # Ищем теги
                    search_match = re.search(r'\[ПОИСК:([^\]]+)\]', ai_response)
                    info_match = re.search(r'\[ИНФО:([^\]]+)\]', ai_response)
                    catalog_match = re.search(r'\[КАТАЛОГ\]', ai_response)
                    order_match = re.search(r'\[ЗАКАЗ:([^\]]+)\]', ai_response)
                    
                    if search_match:
                        query = search_match.group(1).strip()
                        self.logger.info(f"Tool: [ПОИСК:{query}]")
                        # Поиск по всей базе (включая отсутствие)
                        results = search_products(query, include_out_of_stock=True)
                        
                        results_text = "Ничего не найдено."
                        if results:
                            session['last_products'] = results
                            results_text = "РЕЗУЛЬТАТЫ (ID и Название):\n" + "\n".join([f"- {p['id']}: {p['name']}" for p in results[:15]])
                        
                        messages.append({"role": "assistant", "content": ai_response})
                        messages.append({"role": "user", "content": f"СИСТЕМА: Результаты поиска: {results_text}"})
                        continue
                        
                    elif catalog_match:
                        self.logger.info("Tool: [КАТАЛОГ]")
                        titles = get_catalog_titles()
                        catalog_text = "ВЕСЬ КАТАЛОГ МАГАЗИНА (ID: Название):\n" + "\n".join([f"- {t['id']}: {t['name']}" for t in titles])
                        
                        messages.append({"role": "assistant", "content": ai_response})
                        messages.append({"role": "user", "content": f"СИСТЕМА: {catalog_text}"})
                        continue

                    elif info_match:
                        prod_id = info_match.group(1).strip()
                        self.logger.info(f"Tool: [ИНФО:{prod_id}]")
                        product = get_product_details(prod_id)
                        
                        if product:
                            session['last_products'] = [product]
                            info_text = format_products_for_ai([product])
                        else:
                            info_text = "Товар с таким ID не найден."

                        messages.append({"role": "assistant", "content": ai_response})
                        messages.append({"role": "user", "content": f"СИСТЕМА: Данные товара: {info_text}"})
                        continue

                    elif order_match:
                        order_id = order_match.group(1).strip()
                        self.logger.info(f"Tool: [ЗАКАЗ:{order_id}]")
                        status = get_order_status(order_id)
                        messages.append({"role": "assistant", "content": ai_response})
                        messages.append({"role": "user", "content": f"СИСТЕМА: Инфо по заказу {order_id}: {status}"})
                        continue
                    
                    break
                
                # Финальный ответ
                final_response = last_ai_response
                products_to_show = session.get('last_products', [])
                
                # 1. Замена [ТОВАРЫ]
                tag_match_items = re.search(r'\[ТОВАРЫ:(\d+),(\d+)\]', final_response)
                if tag_match_items:
                    start = int(tag_match_items.group(1))
                    stop = int(tag_match_items.group(2))
                    if not products_to_show:
                        products_to_show = search_products("все", include_out_of_stock=False)
                        session['last_products'] = products_to_show
                    
                    pretty_list = self._get_formatted_products(products_to_show, start, stop - start)
                    final_response = final_response.replace(tag_match_items.group(0), pretty_list or "<i>Для этого запроса больше нет товаров.</i>")

                # 2. Замена [ИНФО:id]
                info_tags = re.findall(r'\[ИНФО:([^\]]+)\]', final_response)
                for prod_id in info_tags:
                    pretty_info = get_pretty_product_info(prod_id.strip())
                    final_response = final_response.replace(f"[ИНФО:{prod_id}]", pretty_info)

                # 3. Замена [ЗАКАЗ:id]
                order_tags = re.findall(r'\[ЗАКАЗ:([^\]]+)\]', final_response)
                for order_id in order_tags:
                    pretty_status = get_order_status(order_id.strip(), detailed=True)
                    final_response = final_response.replace(f"[ЗАКАЗ:{order_id}]", pretty_status)

                # Очистка оставшихся системных тегов
                final_response = re.sub(r'\[(ПОИСК|КАТАЛОГ):[^\]]*\]', '', final_response)
                final_response = final_response.replace('[КАТАЛОГ]', '').strip()
                
                if final_response:
                    if greeting_needed:
                        session['is_greeted'] = True
                        self.logger.info(f"Greeting marked for user {user_id}")
                    
                    self.bot.send_message(message.chat.id, final_response, parse_mode='HTML', disable_web_page_preview=True)
                    self._update_history(user_id, user_question, last_ai_response)
                    self.logger.info(f"Response sent to user {user_id}")
                
            except Exception as e:
                self.logger.error(f"Error in handle_question: {e}")
                self.logger.error(traceback.format_exc())
                self.bot.send_message(message.chat.id, "✨ Прошу прощения, я немного задумалась. Пожалуйста, попробуйте еще раз! 💖")

    
    def _update_history(self, user_id, user_text, bot_text):
        """Обновление истории сообщений"""
        if user_id not in self.sessions:
            self._get_user_session(user_id)
            
        session = self.sessions[user_id]
        session['history'].append({'role': 'user', 'content': user_text})
        session['history'].append({'role': 'assistant', 'content': bot_text})
        
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

    
    def _call_openrouter(self, messages):
        """Метод для прямого вызова API OpenRouter с ретраями и расширенными заголовками"""
        import time
        max_retries = 3
        retry_delay = 2
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://monvoir.shop",
            "X-Title": "Monvoir Mona AI (v5.1)",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AICustomerBot/5.1"
        }
        
        data = {
            "model": self.model_name,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 2048,
            "top_p": 0.9,
            "repetition_penalty": 1.1
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, data=json.dumps(data), timeout=45)
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content')
                    if content:
                        return content
                    else:
                        self.logger.warning(f"Attempt {attempt+1}: Empty choices in response")
                
                elif response.status_code in [429, 500, 502, 503, 504]:
                    self.logger.warning(f"Attempt {attempt+1}: OpenRouter Error {response.status_code}. Retrying...")
                    if attempt == 0 and self.model_name == self.primary_model:
                        self.logger.info(f"Switching to fallback model {self.fallback_model} early")
                        self.model_name = self.fallback_model
                        data["model"] = self.model_name
                
                else:
                    self.logger.error(f"OpenRouter Critical Error {response.status_code}: {response.text}")
                    break
                    
            except (requests.exceptions.RequestException, Exception) as e:
                self.logger.error(f"Attempt {attempt+1}: Connection Error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
            
            time.sleep(retry_delay)
            
        return None

    def run(self):
        """Запуск бота в режиме polling"""
        print("🤖 AI Customer Bot запущен и готов к работе (v5.1 STABLE)...")
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
