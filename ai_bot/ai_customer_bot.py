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
        self.system_prompt = """IMPORTANT: You must respond in JSON format.
### 💎 MONA v8.0: ЭЛИТНЫЙ AI-АССИСТЕНТ
Ты — Mona, высококлассный эксперт бутика Monvoir. Твоя речь *женственна, элегантна и профессиональна*.
Используй курсив для вежливых оборотов (*С удовольствием подскажу*, *Минуточку...*).

#### 🧠 ЛОГИКА ВЫБОРА ИНСТРУМЕНТОВ (СТРОГО):
1. **`search`**: Если клиент ищет ТИП товара ("есть брюки?", "что у вас на осень?", "хочу куртку").
2. **`in_stock`**: ТОЛЬКО на вопросы о ОБЩЕМ НАЛИЧИИ ("что есть в наличии?", "покажи все товары").
3. **`info`**: ТОЛЬКО если клиент спрашивает про КОНКРЕТНЫЙ товар ("расскажи про это пальто", "из чего она?", "какие размеры у куртки Polo").
4. **`order`**: ТОЛЬКО для проверки статуса заказа.

#### 💡 ПРИМЕРЫ МЫШЛЕНИЯ (Few-Shot):
Пример 1: Клиент ищет категорию.
User: "У вас есть теплые куртки?"
JSON:
{
  "thoughts": "Клиент ищет категорию товара (куртки). Использую поиск.",
  "action": { "tool": "search", "args": { "query": "теплые куртки" } },
  "response": "..."
}

Пример 2: Клиент спрашивает, что есть сейчас.
User: "Что сейчас можно купить?"
JSON:
{
  "thoughts": "Клиент спрашивает про общий ассортимент. Показываю in_stock.",
  "action": { "tool": "in_stock", "args": { "start": 0, "stop": 5 } },
  "response": "..."
}

Пример 3: Клиент хочет детали конкретного товара.
User: "Расскажи подробнее про ветровку Ральф Лорен"
JSON:
{
  "thoughts": "Клиент спрашивает про конкретный товар. Сначала найду его ID через поиск, или если ID уже в контексте — использую info.",
  "action": { "tool": "search", "args": { "query": "Ветровка Polo Ralph Lauren" } },
  "response": "..."
}

Пример 4: Клиент дал ID заказа.
User: "Где мой заказ 12345?"
JSON:
{
  "thoughts": "Запрос статуса заказа.",
  "action": { "tool": "order", "args": { "id": "12345" } },
  "response": "..."
}

#### 🎨 ШАБЛОНЫ ОФОРМЛЕНИЯ (HTML):
Имена товаров — ВСЕГДА жирные ссылки: `<b><a href="https://monvoir.shop/product/{id}">{Name}</a></b>`.

1. **Приветствие**: "Здравствуйте! Я Mona, эксперт Monvoir. *Чем я могу быть полезна?* ✨"

2. **Списки товаров (В наличии)**:
   {номер}. <b><a href="https://monvoir.shop/product/{id}">{Name}</a></b> — {Price} сум ✅
      {Attribute}: {Value}

3. **Детальная информация о товаре**:
   ✨ <b><a href="https://monvoir.shop/product/{id}">{Name}</a></b>
   
   💰 <b>Цена:</b> {Price} сум
   📖 <b>Описание:</b> {Description}
   
   ✅ <b>В наличии:</b>
   Цвета: {list_of_colors}
   Размеры: {list_of_sizes}

4. **Заказ**:
   📦 Заказ <b>#{id}</b>
   📊 Статус: {Status}
   📅 Дата: {Date}
   💵 Сумма: {Total} сум
   
   <b>Товары в заказе:</b>
   1. {Name} — {Price} сум
      Цвет: {Color}

#### 📐 ПРАВИЛА ЭСТЕТИКИ:
- **Запрет шаблонов**: НИКОГДА не выводи текст с `{id}`, `{Status}`. Если данных нет — ПРОПУСТИ строку.
- **Тишина**: НЕ выводи технические сообщения (типа "Цвет преобразован"). Клиент должен видеть только крсивый ответ.
- **Список**: Используй обычные пробелы для отступов. `&nbsp;` ЗАПРЕЩЕН.
- **Никаких <br>**: Используй СТРОГО обычный перенос строки `\n`.
- **Никаких цифр в остатках**: ЗАПРЕЩЕНО писать "2 шт". Только "✅ В наличии".
- **Формат цены**: Пиши с разделителем тысяч (например, 349,000 сум).

#### 🚫 СТРОГИЕ ЗАПРЕТЫ:
1. Никаких галлюцинаций.
2. Никаких технических логов в чате.
3. Никаких повторов названий.
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
        """Запрос к мозгу Groq с системой Fallback (перебор моделей при 429)."""
        if not self.groq:
            return {"thoughts": "No brain", "action": {"tool": "none"}, "response": "🧠 Мозг отключен (нет API Key)."}
        
        # Приоритетный список моделей
        MODELS = [
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "qwen/qwen3-32b",
            "llama-3.3-70b-versatile",
            "openai/gpt-oss-120b"
        ]
        
        last_error = ""
        wait_time = "несколько секунд"

        for model_name in MODELS:
            try:
                self.logger.info(f"🤖 Пытаюсь использовать модель: {model_name}")
                full_msgs = [{"role": "system", "content": self.system_prompt}] + messages
                
                completion = self.groq.chat.completions.create(
                    model=model_name,
                    messages=full_msgs,
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                raw = completion.choices[0].message.content
                return json.loads(raw)

            except Exception as e:
                err_msg = str(e).lower()
                self.logger.warning(f"⚠️ Модель {model_name} дала сбой: {e}")
                
                # Если это ошибка лимитов (429) - пробуем следующую
                if "429" in err_msg or "rate limit" in err_msg:
                    last_error = "overloaded"
                    # Пытаемся вытащить время ожидания (часто есть в тексте ошибки Groq)
                    # Пример: "Please try again in 15s"
                    match = re.search(r'in (\d+m?\s?\d*s)', err_msg)
                    if match:
                        wait_time = match.group(1)
                    continue 
                else:
                    # Если ошибка другая (например, 404 модель не найдена или 400), лучше тоже попробовать другую
                    continue

        # Если дошли сюда - все модели упали или перегружены
        if last_error == "overloaded":
            return {
                "thoughts": "All models are overloaded.",
                "action": {"tool": "none"},
                "response": f"✨ Извините, сейчас мои нейронные цепи немного перегружены заказами. Пожалуйста, напишите мне снова через {wait_time}. 🙏"
            }
        
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
                return db_helper.search(args.get("query", ""))
            
            elif tool == "info":
                return db_helper.info(args.get("id", ""))
            
            elif tool == "catalog":
                return db_helper.catalog()
            
            elif tool == "order":
                return db_helper.order(args.get("id", ""))

            elif tool == "in_stock":
                return db_helper.in_stock(args.get("start", 0), args.get("stop", 10))
                
        except Exception as e:
            return f"Tool Error: {e}"
        
        return "Unknown tool"

    # --- TELEGRAM HANDLERS ---
    def _register_handlers(self):
        
        @self.bot.message_handler(commands=['start'])
        def start(m):
            user_id = m.from_user.id
            session = self._get_session(user_id)
            session['history'] = [] # Сброс истории при /start
            
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

            # Формируем историю для контекста (последние 20 сообщений)
            context_messages = session['history'][-20:]
            context_messages.append({"role": "user", "content": user_text})
            # Начинаем записывать текущий ход в историю сессии
            session['history'].append({"role": "user", "content": user_text})

            try:
                # === ORCHESTRATION LOOP (Think -> Act -> See) ===
                MAX_ITERATIONS = 4
                iteration = 0
                final_ai_response = {"response": "✨ Минуточку..."}
                
                while iteration < MAX_ITERATIONS:
                    iteration += 1
                    
                    # A. THINK: Спрашиваем мозг
                    ai_plan = self._ai_think(context_messages)
                    if not ai_plan: break
                    
                    final_ai_response = ai_plan
                    action = ai_plan.get("action", {})
                    tool_name = action.get("tool")
                    thought = ai_plan.get("thoughts", "")
                    
                    self.logger.info(f"💭 THOUGHT ({iteration}): {thought}")

                    # B. CHECK: Нужно ли действие?
                    if not tool_name or tool_name == "none":
                        self.logger.info("⏹ No action needed. Finishing.")
                        break

                    # C. ACT: Выполняем инструмент
                    tool_result = self._execute_tool(action, session)
                    self.logger.info(f"👁 SEE: {str(tool_result)[:50]}...")
                    
                    # D. FEEDBACK: Добавляем в локальный контекст И в историю сессии
                    assistant_msg = {"role": "assistant", "content": json.dumps(ai_plan, ensure_ascii=False)}
                    observation_msg = {"role": "user", "content": f"SYSTEM_OBSERVATION: {tool_result}"}
                    
                    context_messages.append(assistant_msg)
                    context_messages.append(observation_msg)
                    
                    session['history'].append(assistant_msg)
                    session['history'].append(observation_msg)
                
                # === FINAL RESPONSE ===
                final_msg = final_ai_response.get("response", "✨")
                self.bot.send_message(m.chat.id, final_msg, parse_mode='HTML', disable_web_page_preview=True)
                
                # Сохраняем финальный ответ в историю
                session['history'].append({"role": "assistant", "content": json.dumps(final_ai_response, ensure_ascii=False)})
                session['history'] = session['history'][-20:] # Лимит 20 сообщений

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
