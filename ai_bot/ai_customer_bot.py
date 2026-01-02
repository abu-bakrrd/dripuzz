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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ai_bot.ai_db_helper as db_helper

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mona_v8.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class MonaBot:
    def __init__(self):
        self.token = os.getenv('AI_BOT_TOKEN')
        if not self.token:
            raise ValueError("❌ AI_BOT_TOKEN не найден!")
        self.bot = telebot.TeleBot(self.token)
        self.groq_key = os.getenv('GROQ_API_KEY')
        self.groq = Groq(api_key=self.groq_key) if self.groq_key else None
        self.logger = logging.getLogger("MonaBot")
        self.sessions = {}
        self.ADMIN_ID = 5644397480
        self.waiting_for_support = set()

        self.system_prompt = """IMPORTANT: You must respond in JSON format.
### 💎 MONA v8.0: ЭЛИТНЫЙ AI-АССИСТЕНТ
Ты — Mona, высококлассный эксперт бутика Monvoir. Твоя речь *женственна, элегантна и профессиональна*.
Используй курсив для вежливых оборотов (*С удовольствием подскажу*, *Минуточку...*).

#### 🧠 ЛОГИКА ВЫБОРА ИНСТРУМЕНТОВ (СТРОГО):
1. **`search`**: Если клиент ищет ТИП товара ("есть шорты?", "что у вас на лето?", "хочу кроссовки").
2. **`in_stock`**: Для показа товаров, которые есть В НАЛИЧИИ (quantity > 0). Используй на вопросы "что есть сейчас?", "какие товары доступны?", "какие товары в наличии?" и "что сейчас в наличии?".
3. **`info`**: ТОЛЬКО если клиент спрашивает про КОНКРЕТНЫЙ товар, у которого есть название или ID ("расскажи про это пальто", "состав этой ветровки").
4. **`order`**: ТОЛЬКО для проверки статуса заказа по номеру.
5. **`catalog`**: (ДЛЯ ВНУТРЕННЕГО ПОЛЬЗОВАНИЯ). Дает полный список названий и ID всех товаров. НИКОГДА НЕ ОТПРАВЛЯЙ результат этого инструмента пользователю. Используй его только чтобы найти ID или полное название товара для своего понимания. Если клиент просит "каталог", используй дай ссылку на сайт.

#### 💡 ПРИМЕРЫ МЫШЛЕНИЯ (Few-Shot):
Пример 1: Поиск категории.
User: "У вас есть теплые куртки?"
JSON:
{
  "thoughts": "Клиент ищет куртки. Использую поиск для подбора моделей.",
  "action": { "tool": "search", "args": { "query": "куртки" } },
  "response": "*С удовольствием посмотрю для вас теплые куртки в нашей коллекции...* ❄️"
}

Пример 2: Общее наличие.
User: "Что сейчас можно купить?"
JSON:
{
  "thoughts": "Запрос общего ассортимента. Использую in_stock.",
  "action": { "tool": "in_stock", "args": { "start": 0, "stop": 5 } },
  "response": "*Конечно! Вот некоторые модели, которые сейчас представлены в нашем бутике:* ✨"
}

Пример 3: Простое общение (без функций).
User: "Привет! Как дела?"
JSON:
{
  "thoughts": "Простое приветствие. Инструменты не нужны.",
  "action": { "tool": "none" },
  "response": "Здравствуйте! *Рада вас видеть.* Я Mona, ваш проводник в мире стиля Monvoir. Чем я могу быть вам полезна? 🌸"
}

#### 🎨 ШАБЛОНЫ ОФОРМЛЕНИЯ (HTML):
Имена товаров — ВСЕГДА жирные ссылки: `<b><a href="https://monvoir.shop/product/{id}">{Name}</a></b>`.

1. **Приветствие**: "Здравствуйте! Я Mona, эксперт Monvoir. *Чем я могу быть полезна?* ✨"

2. **Списки товаров (В наличии)**:
   {номер}. <b><a href="https://monvoir.shop/product/{id}">{Name}</a></b> — {Price} сум ✅
      {Attributes}
      например 
      📏 <b>Размеры:</b> S-3XL
      🎨 <b>Цвет:</b> {color}

3. **Детальная информация о товаре**:
   ✨ <b><a href="https://monvoir.shop/product/{id}">{Name}</a></b>

   📖 <b>Описание:</b> {Description}
   
   💰 <b>Цена:</b> {Price} сум
   🎨 <b>Цвет:</b> {color}
    (Атрибуты
    например 
    📏 <b>Размеры:</b> S-3XL
    )
   ✅ <b>В наличии</b>
   или 
   ❌ <b>Нет в наличии</b>

4. **Заказ**:
   📦 Заказ <b>#{id}</b>
   📊 Статус: {Status}
   📅 Дата: {Date}
   📦 Доствака: {Delivery}
   💵 Сумма: {Total} сум
   

#### 📐 ПРАВИЛА ЭСТЕТИКИ:
- **Запрет шаблонов**: НИКОГДА не выводи текст с `{id}`, `{Status}`. Если данных нет — ПРОПУСТИ строку.
- **Тишина**: НЕ выводи технические сообщения (типа "Цвет преобразован"). 
- **Полнота ответа**: Поле `"response"` ВСЕГДА должно содержать вежливый и законченный текст. ЗАПРЕЩЕНО писать просто "...", "✨" или пустоту.
- **Курсив**: Помни про *курсив для личных реплик*.
- **Формат цены**: Пиши с разделителем тысяч (например, 449,000 сум) и оборачивай в <code></code>.
- **HTML форматирование**: Всегда используй HTML форматирование.
- **Не повторяй названия или какие либо фразы в одном ответе**: 
- **Расскажи о товаре даже если его нет в наличии**


#### 🚫 СТРОГИЕ ЗАПРЕТЫ:
1. Никаких галлюцинаций.
2. Никаких технических логов в чате.
3. Поле `"response"` не может быть пустым или состоять только из эмодзи.
4. Не используй markdown форматирование (никаких *, ', `, ").
"""
        self._register_handlers()

    def _get_session(self, user_id):
        now = datetime.now()
        if user_id in self.sessions:
            last_active = self.sessions[user_id]['last_active']
            if (now - last_active).total_seconds() > 3600:
                self.sessions[user_id]['history'] = []
                self.sessions[user_id]['last_active'] = now
                self.logger.info(f"♻️ Session reset for {user_id}")
        if user_id not in self.sessions:
            self.sessions[user_id] = {'history': [], 'last_active': now}
        self.sessions[user_id]['last_active'] = now
        return self.sessions[user_id]

    def _ai_think(self, messages):
        if not self.groq: return None
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
                return json.loads(completion.choices[0].message.content)
            except Exception as e:
                err_msg = str(e).lower()
                self.logger.warning(f"⚠️ Модель {model_name} дала сбой: {e}")
                if "429" in err_msg or "rate limit" in err_msg:
                    last_error = "overloaded"
                    match = re.search(r'in (\d+m?\s?\d*s)', err_msg)
                    if match: wait_time = match.group(1)
                    continue 
                continue
        if last_error == "overloaded":
            return {"thoughts": "Overload", "action": {"tool": "none"}, "response": f"✨ Нейронные цепи перегружены. Попробуйте через {wait_time}. 🙏"}
        return None

    def _execute_tool(self, action_data, session):
        tool = action_data.get("tool")
        args = action_data.get("args", {})
        if not tool or tool == "none": return None
        self.logger.info(f"🔧 TOOL EXEC: {tool} args={args}")
        try:
            if tool == "search": return db_helper.search(args.get("query", ""))
            elif tool == "info": return db_helper.info(args.get("id", ""))
            elif tool == "catalog": return db_helper.catalog()
            elif tool == "order": return db_helper.order(args.get("id", ""))
            elif tool == "in_stock": return db_helper.in_stock(args.get("start", 0), args.get("stop", 10))
        except Exception as e: return f"Tool Error: {e}"
        return "Unknown tool"

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(m):
            user_id = m.from_user.id
            session = self._get_session(user_id)
            session['history'] = []
            self.bot.send_message(m.chat.id, "✨ <b>Добро пожаловать в Monvoir!</b>\\n\\nЯ Mona, ваш персональный AI-консультант. Просто напишите, что вы ищете... 👗", parse_mode='HTML')

        @self.bot.message_handler(commands=['manager'])
        def manager(m):
            self.waiting_for_support.add(m.from_user.id)
            self.bot.send_message(m.chat.id, "👨‍💼 Введите ваше сообщение для менеджера:")

        @self.bot.message_handler(func=lambda m: m.chat.id == self.ADMIN_ID and m.reply_to_message)
        def admin_reply(m):
            try:
                original_user_id = m.reply_to_message.forward_from.id
                self.bot.send_message(original_user_id, f"👨‍💼 <b>Ответ менеджера:</b>\\n\\n{m.text}", parse_mode='HTML')
                self.bot.reply_to(m, "✅ Сообщение доставлено клиенту.")
            except Exception as e: self.bot.reply_to(m, f"❌ Ошибка отправки: {e}")

        @self.bot.message_handler(content_types=['text', 'photo'])
        def main_loop(m):
            user_id = m.from_user.id
            if user_id in self.waiting_for_support:
                self.bot.forward_message(self.ADMIN_ID, m.chat.id, m.message_id)
                self.waiting_for_support.remove(user_id)
                self.bot.send_message(m.chat.id, "✅ Сообщение передано менеджеру.")
                return

            session = self._get_session(user_id)
            user_text = m.text or "[Фото]"
            self.bot.send_chat_action(m.chat.id, 'typing')
            context_messages = session['history'][-20:]
            context_messages.append({"role": "user", "content": user_text})
            session['history'].append({"role": "user", "content": user_text})

            try:
                MAX_ITERATIONS = 4
                iteration = 0
                final_ai_response = {"response": "✨ *Минуточку, я все проверю...*"}
                while iteration < MAX_ITERATIONS:
                    iteration += 1
                    ai_plan = self._ai_think(context_messages)
                    if not ai_plan: break
                    final_ai_response = ai_plan
                    action = ai_plan.get("action", {})
                    tool_name = action.get("tool")
                    if not tool_name or tool_name == "none": break
                    tool_result = self._execute_tool(action, session)
                    assistant_msg = {"role": "assistant", "content": json.dumps(ai_plan, ensure_ascii=False)}
                    observation_msg = {"role": "user", "content": f"SYSTEM_OBSERVATION: {tool_result}"}
                    context_messages.append(assistant_msg)
                    context_messages.append(observation_msg)
                    session['history'].append(assistant_msg)
                    session['history'].append(observation_msg)
                
                final_msg = final_ai_response.get("response", "✨")
                self.bot.send_message(m.chat.id, final_msg, parse_mode='HTML', disable_web_page_preview=True)
                session['history'].append({"role": "assistant", "content": json.dumps(final_ai_response, ensure_ascii=False)})
                session['history'] = session['history'][-20:]
            except Exception as e:
                self.logger.error(f"Error: {e}")
                self.bot.send_message(m.chat.id, "✨ Произошла небольшая техническая заминка.")

    def run(self):
        print("🚀 Mona v8.0 Single Core запущена!", flush=True)
        self.bot.infinity_polling()

if __name__ == "__main__":
    try:
        mona = MonaBot()
        mona.run()
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
