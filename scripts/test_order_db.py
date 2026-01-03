import sys
import os
from datetime import datetime

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from ai_bot.ai_db_helper import get_order_status
from backend.database import get_db_connection

def test_orders():
    print("🚀 TЕСТ ПОИСКА ЗАКАЗОВ В БАЗЕ (Прямой запрос)")
    
    # 1. Проверяем подключение
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM orders")
        count = cur.fetchone()['count']
        print(f"✅ Подключение к БД успешно! Всего заказов в базе: {count}")
        
        # Выведем последние 3 заказа для примера
        cur.execute("SELECT id FROM orders ORDER BY created_at DESC LIMIT 3")
        rows = cur.fetchall()
        print(f"📋 Последние 3 ID в базе: {[r['id'] for r in rows]}")
        
        conn.close()
    except Exception as e:
        print(f"❌ ОШИБКА Подключения к БД: {e}")
        return

    # 2. Тестируем конкретные ID
    test_ids = [
        "fac35e1b-ac7d-4770-ac34-04c120d22afb", # Правильный (если он есть)
        "fac35e1b",                             # Короткий правильный
        "fаc35e1b7-ac7d-4770-ac34-04c120d22afb", # Ваш (с опечаткой 9 символов)
        "fc35e1b7-ac7d-4770-ac34-04c120d22afb"   # Ваш (с пропущенной буквой)
    ]

    print("\n🔍 НАЧИНАЕМ ПОИСК:")
    for oid in test_ids:
        print(f"\n👉 Ищем ID: '{oid}'")
        res = get_order_status(oid)
        if res:
            print("✅ НАЙДЕН!")
            print(res)
        else:
            print("❌ НЕ найден.")

if __name__ == "__main__":
    test_orders()
