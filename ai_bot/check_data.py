import os
import sys
from dotenv import load_dotenv

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_bot.ai_db_helper import get_all_products_info, format_products_for_ai

load_dotenv()

print("🔍 Проверка данных бота...")
try:
    products = get_all_products_info()
    if not products:
        print("❌ Товаров в базе нет!")
    else:
        print(f"✅ Найдено товаров: {len(products)}")
        print("\n--- Как это видит бот (raw data) ---")
        print(products)
        print("\n--- Как это видит AI (formatted) ---")
        print(format_products_for_ai(products))
except Exception as e:
    print(f"❌ Ошибка при получении данных: {e}")
