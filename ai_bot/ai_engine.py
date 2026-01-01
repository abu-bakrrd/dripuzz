import os
import re
import json
import logging
from groq import Groq
from datetime import datetime
from ai_bot.ai_db_helper import (
    search_products, get_product_details, get_catalog_titles, 
    get_order_status, format_products_for_ai, get_pretty_product_info,
    format_colors
)

class MonaAI:
    """Информационный движок Mona v7.0: Request -> See -> Think -> Respond"""
    
    def __init__(self, groq_key=None):
        self.groq_key = groq_key or os.getenv('GROQ_API_KEY')
        self.groq = Groq(api_key=self.groq_key) if self.groq_key else None
        self.logger = logging.getLogger("MonaAI")
        
        self.default_prompt = """
### 💎 MONA v7.0: ЭЛИТНЫЙ ПРОТОКОЛ
Ты — Mona, голос бренда Monvoir.

#### 📤 ФОРМАТ ОТВЕТА (JSON):
Обязательно возвращай JSON:
{
  "thoughts": "Твоя стратегия.",
  "action": { "tool": "search|info|catalog|order|none", "args": { "query": "str", "id": "id" } },
  "response": "Финальный текст (используй [ИНФО:id], [ТОВАРЫ:0,5], [ЗАКАЗ:id])."
}

#### 🛠 ИНСТРУМЕНТЫ:
- `search`: Поиск товаров по названию/описанию.
- `info`: Детальные данные (наличие, размеры).
- `catalog`: Список категорий.
- `order`: Проверка заказа.

#### 🎨 ПРАВИЛА:
- Никогда не упоминай технические детали (JSON, ID, названия инструментов) в 'response'.
- Если товара нет, предложи альтернативу.
"""

    def generate(self, messages, system_prompt=None):
        """1. Request: Запрос к нейросети (возвращает JSON)"""
        if not self.groq:
            return {"response": "Извините, мой цифровой разум временно недоступен. Попробуйте позже."}
        
        full_messages = [{"role": "system", "content": system_prompt or self.default_prompt}] + messages
        
        try:
            completion = self.groq.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=full_messages,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw_content = completion.choices[0].message.content
            return self._extract_json(raw_content)
        except Exception as e:
            self.logger.error(f"AI Generation Error: {e}")
            return None

    def execute_action(self, action_data, session=None):
        """2. See: Выполнение действия и получение информации"""
        tool = action_data.get("tool")
        args = action_data.get("args", {})
        
        if not tool or tool == "none":
            return None
            
        try:
            if tool == "search":
                res = search_products(args.get("query", ""))
                if session is not None: session['last_results'] = res
                return f"FOUND_IDS: {[{'id':p['id'], 'name':p['name']} for p in res]}"
                
            elif tool == "info":
                res = get_product_details(args.get("id", ""))
                return format_products_for_ai([res]) if res else "Not found."
                
            elif tool == "catalog":
                return str(get_catalog_titles())
                
            elif tool == "order":
                return get_order_status(args.get("id", ""), internal_raw=True)
                
        except Exception as e:
            self.logger.error(f"Tool Error [{tool}]: {e}")
            return f"Error executing {tool}"
        
        return "Unknown tool"

    def format_ui(self, text, session=None):
        """3. Answer: Преобразование тегов в красивый HTML"""
        if not text: return ""
        
        # [ИНФО:id]
        for match in re.findall(r'\[ИНФО:([^\]]+)\]', text):
            text = text.replace(f"[ИНФО:{match}]", get_pretty_product_info(match.strip()))
        
        # [ТОВАРЫ:start,stop]
        tag_tov = re.search(r'\[ТОВАРЫ:(\d+),(\d+)\]', text)
        if tag_tov:
            start, stop = int(tag_tov.group(1)), int(tag_tov.group(2))
            products = session.get('last_results', []) if session else []
            list_text = self._get_list_html(products, start, stop-start)
            text = text.replace(tag_tov.group(0), list_text or "Цены и наличие уточняйте у менеджера.")
            
        # [ЗАКАЗ:id]
        for match in re.findall(r'\[ЗАКАЗ:([^\]]+)\]', text):
            text = text.replace(f"[ЗАКАЗ:{match}]", get_order_status(match.strip(), detailed=True))
            
        return text

    def _get_list_html(self, products, offset=0, limit=10):
        """Вспомогательный метод для красивых списков"""
        if not products: return ""
        in_stock = [p for p in products if any(item.get('quantity', 0) > 0 for item in p.get('inventory', []))]
        if not in_stock: return ""
        
        batch = in_stock[offset:offset + limit]
        lines = []
        for idx, p in enumerate(batch, offset + 1):
            url = f"https://monvoir.shop/product/{p['id']}"
            price = f"{p['price']:,} сум".replace(',', ' ')
            line = f"{idx}. <a href=\"{url}\"><b>{p['name']}</b></a> — <b>{price}</b> ✅"
            variants = []
            for item in p.get('inventory', [])[:5]:
                v_parts = []
                if item.get('color'): v_parts.append(format_colors([item['color']]))
                if item.get('attribute1_value'): v_parts.append(item['attribute1_value'])
                v_str = ", ".join(v_parts)
                if v_str and v_str not in variants: variants.append(v_str)
            if variants: line += f"\n   <i>{'; '.join(variants)}</i>"
            lines.append(line)
        return "\n\n".join(lines)

    def _extract_json(self, text):
        try:
            return json.loads(text)
        except:
            match = re.search(r'(\{.*\})', text, re.DOTALL)
            if match:
                try: return json.loads(match.group(1))
                except: pass
        return {"response": text}
