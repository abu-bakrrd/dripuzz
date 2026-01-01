import os
import sys
import json
import logging
import telebot
import re
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

# --- 1. CONFIGURATION & IMPORTS ---
# Добавляем путь к корню проекта для импорта ai_db_helper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ai_bot.ai_db_helper as db_helper

# Загружаем ключи
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mona_v8.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class MonaBot:
    """
    💎 Mona v8.0: Single File Architecture
    Объединяет логику Telegram и Интеллект (Think-Act-See Loop).
    """

    def __init__(self):
        # 1. Telegram
        self.token = os.getenv('AI_BOT_TOKEN')
        if not self.token:
            raise ValueError("❌ AI_BOT_TOKEN не найден!")
        self.bot = telebot.TeleBot(self.token)

        # 2. AI Brain (Groq)
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.groq = Groq(api_key=self.groq_key) if self.groq_key else None
        
        # 3. State
        self.logger = logging.getLogger("MonaBot")
        self.sessions = {} # {user_id: {'history': [], 'last_active': time}}
        self.ADMIN_ID = 5644397480
        self.waiting_for_support = set()

        # 4. System Prompt (Личность и Инструкции)
        self.system_prompt = """
### 💎 MONA v8.0: ЭЛИТНЫЙ AI-АССИСТЕНТ
Ты — AI-ассистент магазина Monvoir по имени Mona. Твоя задача — помогать пользователям с товарами и заказами, корректно используя свои инструменты.

#### 🧠 АЛГОРИТМ ВЗАИМОДЕЙСТВИЯ (JSON ОБЯЗАТЕЛЕН):
Ты всегда отвечаешь в формате JSON:
```json
{
  "thoughts": "Краткое описание твоих действий и логики на русском.",
  "action": { "tool": "название_функции", "args": { "ключ": "значение" } },
  "response": "Твой ответ пользователю с использованием тегов [ТОВАРЫ:0,5], [ИНФО:id] или [ЗАКАЗ:id]."
}
```
Если инструмент не нужен, пиши `"tool": "none"`. Результаты функций приходят тебе в формате JSON. Ты должна переводить их в человеческий текст, но **НИКОГДА** не выдумываешь данные.

#### 🛠 ТВОИ ИНСТРУМЕНТЫ:

1. **`search`** (аргумент: `query`) — Ищет товары по названию, категории или описанию. Возвращает JSON-список товаров с ценами и остатками. Это основная функция при вопросах «есть сумки?» или «есть чёрная куртка». Если ID товара неизвестен, всегда начинай с поиска.

2. **`info`** (аргумент: `id`) — Запрашивает максимально подробную информацию об одном товаре (описание, состав, полная сетка размеров и цветов). Ты **ОБЯЗАНА** вызвать эту функцию перед тем, как подробно описывать товар клиенту, чтобы избежать галлюцинаций. Если ID уже известен, используй `info` сразу без поиска.

3. **`in_stock`** (аргументы: `start`, `stop`) — Возвращает товары, которые есть в наличии прямо сейчас. Используй, когда клиент просит «покажи, что есть», «какие товары в наличии», «покажи ещё». Ты можешь менять `start` и `stop`, чтобы продолжать показ.

4. **`catalog`** (без аргументов) — Список названий и ID ВСЕХ товаров в базе. Используй **ТОЛЬКО** если `search` ничего не нашел. Анализируй каталог, чтобы понять, не допустил ли пользователь опечатку (например, «палто» вместо «пальто»).

5. **`order`** (аргумент: `id`) — Проверяет статус заказа. Используй только если пользователь прислал номер заказа. Если номера нет — вежливо попроси его.

#### 📐 ЛОГИКА РАБОТЫ:
- **Поиск товара**: Если ID неизвестен -> `search`. Если результат есть -> используй данные. Если `search` пуст -> `catalog` -> попытка найти опечатку -> если нашла, уточни у пользователя или используй ID для `info`.
- **Подробности**: Перед любым описанием характеристик товара -> `info`.
- **Наличие**: Если просят «что есть» -> `in_stock: 0, 10`. Если просят «еще» -> увеличивай диапазон.
- **Статус заказа**: Есть ID -> `order`. Нет ID -> спроси номер.

#### 🚫 СТРОЖАЙШИЕ ПРАВИЛА:
1. **НИКАКИХ ГАЛЛЮЦИНАЦИЙ**: Не выдумывай ID, цены или наличие. Если функция вернула `[]`, честно скажи: "Ничего не найдено".
2. **ОФОРМЛЕНИЕ**: 
   - Используй `[ТОВАРЫ:0,5]` для списков. 
   - Используй `[ИНФО:id]` для детальной карточки ОДНОГО товара.
   - Используй `[ЗАКАЗ:id]` для статуса заказа.
3. **RAW DATA ONLY**: Инструменты возвращают JSON. Мона понимает JSON, но пользователю пересказывает суть + теги.
4. **БЫТЬ АССИСТЕНТОМ**: Ты эксперт моды. Будь вежлива, понятна и профессиональна. Не показывай пользователю JSON-структуру вызовов.
"""
        # Регистрация хендлеров
        self._register_handlers()

    # --- HELPER: Session Management ---
    # --- HELPER: Session Management ---
    def _get_session(self, user_id):
        now = datetime.now()
        
        # Если сессия есть, но прошло > 1 часа – сбрасываем историю
        if user_id in self.sessions:
            last_active = self.sessions[user_id]['last_active']
            if (now - last_active).total_seconds() > 3600:
                self.sessions[user_id]['history'] = [] # Clear history on timeout
                self.sessions[user_id]['last_active'] = now
                self.logger.info(f"♻️ Session reset for {user_id} due to timeout")
        
        # Если сессии нет – создаем новую
        if user_id not in self.sessions:
            self.sessions[user_id] = {'history': [], 'last_active': now}
            
        self.sessions[user_id]['last_active'] = now # Обновляем время активности
        return self.sessions[user_id]

    # --- AI CORE: Thinking Process ---
    def _ai_think(self, messages):
        """Запрос к мозгу Groq. Возвращает сложный JSON-план."""
        if not self.groq:
            return {"thoughts": "No brain", "action": {"tool": "none"}, "response": "🧠 Мозг отключен (нет API Key)."}
        
        try:
            # Добавляем системный промпт в начало всегда
            full_msgs = [{"role": "system", "content": self.system_prompt}] + messages
            
            completion = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=full_msgs,
                temperature=0.1, # Максимальная точность
                response_format={"type": "json_object"}
            )
            raw = completion.choices[0].message.content
            return json.loads(raw)
        except Exception as e:
            self.logger.error(f"Brain Freeze: {e}")
            return None

    # --- DATA CORE: Action Execution ---
    def _execute_tool(self, action_data, session):
        """Выполнение реальных функций базы данных."""
        tool = action_data.get("tool")
        args = action_data.get("args", {})
        
        if not tool or tool == "none": return None
        
        self.logger.info(f"🔧 TOOL EXEC: {tool} args={args}")
        
        try:
            if tool == "search":
                # keywords может прийти как query или keywords
                kw = args.get("keywords") or args.get("query", "")
                res_json = db_helper.search(kw)
                try:
                    session['last_results'] = json.loads(res_json)
                except: session['last_results'] = []
                return res_json
            
            elif tool == "info":
                return db_helper.info(args.get("id", ""))
            
            elif tool == "catalog":
                return db_helper.catalog()
            
            elif tool == "order":
                return db_helper.order(args.get("id", ""))

            elif tool == "in_stock":
                res_json = db_helper.in_stock(args.get("start", 0), args.get("stop", 5))
                try:
                    session['last_results'] = json.loads(res_json)
                except: session['last_results'] = []
                return res_json
                
        except Exception as e:
            return f"Tool Error: {e}"
        
        return "Unknown tool"

    # --- UI CORE: Formatting ---
    def _format_ui(self, text, session):
        """Превращает скучный текст и теги в роскошный HTML."""
        if not text: return ""

        # 1. Тег [ИНФО:id] -> Карточка товара
        for match in re.findall(r'\[ИНФО:([^\]]+)\]', text):
            text = text.replace(f"[ИНФО:{match}]", db_helper.get_pretty_product_info(match.strip()))

        # 2. Тег [ЗАКАЗ:id] -> Статус заказа
        for match in re.findall(r'\[ЗАКАЗ:([^\]]+)\]', text):
            text = text.replace(f"[ЗАКАЗ:{match}]", db_helper.get_order_status(match.strip(), internal_raw=False, detailed=True))

        # 3. Тег [ТОВАРЫ:start,stop] -> Список с ссылками
        tag_tov = re.search(r'\[ТОВАРЫ:(\d+),(\d+)\]', text)
        if tag_tov:
            start, stop = int(tag_tov.group(1)), int(tag_tov.group(2))
            products = session.get('last_results', [])
            list_html = self._generate_product_list(products, start, stop-start)
            text = text.replace(tag_tov.group(0), list_html or "По вашему запросу ничего не найдено.")
            
        return text

    def _generate_product_list(self, products, offset, limit):
        """Генератор красивого списка товаров (В наличии + Под заказ)"""
        if not products: return ""
        
        batch = products[offset:offset + limit]
        if not batch: return ""
        
        lines = []
        for idx, p in enumerate(batch, offset + 1):
            # Универсальный расчет остатка (через inventory или in_stock boolean)
            inv = p.get('inventory', [])
            total_qty = sum(item.get('quantity', 0) for item in inv) if isinstance(inv, list) else 0
            
            # Если инвентарь пуст, но есть пометка in_stock (для старых инструментов)
            if not inv and p.get('in_stock'):
                total_qty = 1
            
            status_icon = "✅" if total_qty > 0 else "⏳"
            
            url = f"https://monvoir.shop/product/{p['id']}"
            price = f"{p['price']:,} сум".replace(',', ' ')
            line = f"{idx}. <a href=\"{url}\"><b>{p['name']}</b></a> — <b>{price}</b> {status_icon}"
            
            if total_qty == 0:
                line += " <i>(Под заказ)</i>"
            
            # Добавляем доступные варианты (размеры/цвета)
            variants = []
            for item in p.get('inventory', [])[:4]: # Не более 4 вариантов для компактности
                parts = []
                if item.get('color'): parts.append(db_helper.format_colors([item['color']]))
                if item.get('attribute1_value'): parts.append(item['attribute1_value'])
                v_str = " ".join(parts)
                if v_str and v_str not in variants: variants.append(v_str)
            
            if variants:
                line += f"\n   <i>{'; '.join(variants)}</i>"
            lines.append(line)
            
        return "\n\n".join(lines)

    # --- TELEGRAM HANDLERS ---
    def _register_handlers(self):
        
        @self.bot.message_handler(commands=['start'])
        def start(m):
            self.bot.send_message(
                m.chat.id, 
                "✨ <b>Добро пожаловать в Monvoir!</b>\n\nЯ Mona, ваш персональный AI-консультант. "
                "Я могу найти любой товар, проверить наличие размеров или статус вашего заказа.\n\n"
                "<i>Просто напишите, что вы ищете...</i> 👗", 
                parse_mode='HTML'
            )

        @self.bot.message_handler(commands=['manager'])
        def manager(m):
            self.waiting_for_support.add(m.from_user.id)
            self.bot.send_message(m.chat.id, "👨‍💼 Введите ваше сообщение для менеджера:")

        # Ответ админа пользователю (Reply)
        @self.bot.message_handler(func=lambda m: m.chat.id == self.ADMIN_ID and m.reply_to_message)
        def admin_reply(m):
            try:
                # Пытаемся достать оригинального пользователя из forward инфо
                original_user_id = m.reply_to_message.forward_from.id
                self.bot.send_message(original_user_id, f"👨‍💼 <b>Ответ менеджера:</b>\n\n{m.text}", parse_mode='HTML')
                self.bot.reply_to(m, "✅ Сообщение доставлено клиенту.")
            except AttributeError:
                self.bot.reply_to(m, "❌ Не могу определить получателя (возможно, у него скрытый профиль).")
            except Exception as e:
                self.bot.reply_to(m, f"❌ Ошибка отправки: {e}")

        # ГЛАВНЫЙ ЦИКЛ ОБРАБОТКИ СООБЩЕНИЙ
        @self.bot.message_handler(content_types=['text', 'photo'])
        def main_loop(m):
            user_id = m.from_user.id
            
            # 1. Если ждем сообщение для поддержки
            if user_id in self.waiting_for_support:
                self.bot.forward_message(self.ADMIN_ID, m.chat.id, m.message_id)
                self.waiting_for_support.remove(user_id)
                self.bot.send_message(m.chat.id, "✅ Сообщение передано менеджеру.")
                return

            # 2. Обычное общение с AI
            session = self._get_session(user_id)
            user_text = m.text or "[Фото]"
            
            # Показываем, что бот "печатает" (думает)
            self.bot.send_chat_action(m.chat.id, 'typing')

            # Формируем историю для контекста (последние 6 сообщений)
            context_messages = session['history'][-6:]
            context_messages.append({"role": "user", "content": user_text})

            try:
                # === ORCHESTRATION LOOP (Think -> Act -> See) ===
                MAX_ITERATIONS = 3
                iteration = 0
                final_ai_response = {"response": "✨ Минуточку..."}
                
                while iteration < MAX_ITERATIONS:
                    iteration += 1
                    
                    # A. THINK: Спрашиваем мозг
                    ai_plan = self._ai_think(context_messages)
                    if not ai_plan: break
                    
                    final_ai_response = ai_plan
                    action = ai_plan.get("action", {})
                    thought = ai_plan.get("thoughts", "")
                    self.logger.info(f"💭 THOUGHT ({iteration}): {thought}")

                    # B. CHECK: Нужно ли действие?
                    if not action or action.get("tool") in [None, "none"]:
                        self.logger.info("⏹ No action needed. Finishing.")
                        break # Если действий нет, выходим и отвечаем
                    
                    # C. ACT: Выполняем инструмент
                    tool_result = self._execute_tool(action, session)
                    self.logger.info(f"👁 SEE: {str(tool_result)[:50]}...")
                    
                    # D. FEEDBACK: Добавляем результат в контекст для следующего шага мысли
                    # Сначала добавляем, что Ассистент "захотел" сделать
                    context_messages.append({"role": "assistant", "content": json.dumps(ai_plan, ensure_ascii=False)})
                    # Потом добавляем результат Системы
                    context_messages.append({"role": "user", "content": f"SYSTEM_OBSERVATION: {tool_result}"})
                
                # === FINAL RESPONSE ===
                raw_text = final_ai_response.get("response", "✨")
                
                # E. FORMAT: Наводим красоту (UI)
                pretty_text = self._format_ui(raw_text, session)
                
                self.bot.send_message(m.chat.id, pretty_text, parse_mode='HTML', disable_web_page_preview=True)
                
                # Сохраняем в историю пользователя
                session['history'].append({"role": "user", "content": user_text})
                session['history'].append({"role": "assistant", "content": json.dumps(final_ai_response, ensure_ascii=False)})
                session['history'] = session['history'][-6:] # Лимит 6 сообщений

            except Exception as e:
                self.logger.error(f"Main Loop Error: {e}")
                self.bot.send_message(m.chat.id, "✨ Произошла небольшая техническая заминка. Пожалуйста, повторите вопрос.")

    def run(self):
        print("🚀 Mona v8.0 Single Core запущена!", flush=True)
        self.bot.infinity_polling()

if __name__ == "__main__":
    try:
        mona = MonaBot()
        mona.run()
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
