"""
Скрипт для проверки статуса бота и просмотра последних логов
"""
import os
import sys
import io

# Устанавливаем UTF-8 для вывода в Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Загрузка переменных окружения
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path)

print("=" * 50)
print("ПРОВЕРКА СТАТУСА БОТА")
print("=" * 50)
print()

# Проверка переменных окружения
print("📋 Проверка переменных окружения:")
print(f"  - AI_BOT_TOKEN: {'✅ Установлен' if os.getenv('AI_BOT_TOKEN') else '❌ Не найден'}")
print(f"  - GROQ_API_KEY: {'✅ Установлен' if os.getenv('GROQ_API_KEY') else '❌ Не найден'}")
print(f"  - DATABASE_URL: {'✅ Установлен' if os.getenv('DATABASE_URL') else '❌ Не найден'}")
print()

# Проверка подключения к Groq
print("🤖 Проверка Groq API:")
try:
    from groq import Groq
    api_key = os.getenv('GROQ_API_KEY')
    if api_key:
        client = Groq(api_key=api_key)
        model_name = "meta-llama/llama-4-scout-17b-16e-instruct"
        print(f"  ✅ Groq клиент инициализирован")
        print(f"  📌 Модель: {model_name}")
    else:
        print("  ❌ GROQ_API_KEY не найден")
except Exception as e:
    print(f"  ❌ Ошибка инициализации Groq: {e}")
print()

# Проверка подключения к Telegram Bot API
print("📱 Проверка Telegram Bot API:")
try:
    import telebot
    bot_token = os.getenv('AI_BOT_TOKEN')
    if bot_token:
        bot = telebot.TeleBot(bot_token)
        bot_info = bot.get_me()
        print(f"  ✅ Бот подключен")
        print(f"  📌 Имя: {bot_info.first_name}")
        print(f"  📌 Username: @{bot_info.username}")
        print(f"  📌 ID: {bot_info.id}")
    else:
        print("  ❌ AI_BOT_TOKEN не найден")
except Exception as e:
    print(f"  ❌ Ошибка подключения к Telegram: {e}")
print()

# Проверка подключения к БД
print("💾 Проверка базы данных:")
try:
    from ai_bot.ai_db_helper import get_all_products_info
    products = get_all_products_info()
    print(f"  ✅ База данных подключена")
    print(f"  📦 Товаров в каталоге: {len(products) if products else 0}")
except Exception as e:
    print(f"  ❌ Ошибка подключения к БД: {e}")
print()

print("=" * 50)
print("✅ Проверка завершена")
print("=" * 50)
print()
print("💡 Для просмотра логов в реальном времени:")
print("   1. Запустите бота: python ai_customer_bot.py")
print("   2. Или используйте: start_ai_bot.bat (Windows)")
print("   3. Логи будут отображаться в консоли")

