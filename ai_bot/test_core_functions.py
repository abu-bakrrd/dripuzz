import sys
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add path to root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_bot.ai_db_helper import search, catalog, order, info, in_stock

def run_examples():
    print("🚀 === ТЕСТ КОРНЕВЫХ ФУНКЦИЙ AI ===\n")

    print("1. 🔍 search('футболка'):")
    print(search('футболка'))
    print("-" * 30)

    print("\n2. 📁 catalog():")
    print(catalog())
    print("-" * 30)

    print("\n3. 📦 in_stock(0, 5):")
    print(in_stock(0, 5))
    print("-" * 30)

    # Let's try to get an ID from catalog for info
    try:
        cat_lines = catalog().split('\n')
        if cat_lines and '-' in cat_lines[0]:
            first_id = cat_lines[0].split(' - ')[1].strip()
            print(f"\n4. ℹ️ info('{first_id}'):")
            print(info(first_id)[:500] + "...") # Truncate for display
        else:
            print("\n4. ℹ️ info: No products found for test.")
    except Exception as e:
        print(f"\n4. ℹ️ info error: {e}")
    print("-" * 30)

    print("\n5. 📜 order('123'):")
    print(order('123'))
    print("-" * 30)

if __name__ == "__main__":
    run_examples()
