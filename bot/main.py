import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "👋 Добро пожаловать!\n\n"
        "Доступные команды:\n"
        "/start - Начать работу\n"
        "/about - О нас\n"
        "/help - Помощь\n"
        "/support - Поддержка\n"
        "/contact - Контакты"
    )

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /about"""
    await update.message.reply_text(
        "ℹ️ О нас\n\n"
        "Это информационный бот для нашего магазина.\n"
        "Здесь вы можете получить всю необходимую информацию."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "❓ Помощь\n\n"
        "Используйте следующие команды:\n\n"
        "/start - Главное меню\n"
        "/about - Узнать о нас\n"
        "/help - Показать это сообщение\n"
        "/support - Получить поддержку\n"
        "/contact - Наши контакты"
    )

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /support"""
    await update.message.reply_text(
        "💬 Поддержка\n\n"
        "Если у вас возникли вопросы или проблемы, "
        "напишите нам или используйте команду /contact для получения контактов."
    )

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /contact"""
    await update.message.reply_text(
        "📞 Наши контакты\n\n"
        "Telegram: @your_contact\n"
        "Email: support@example.com\n"
        "Телефон: +998 XX XXX XX XX"
    )

def main():
    """Запуск бота"""
    token = os.getenv('INFO_BOT_TOKEN')
    
    if not token:
        logger.error("❌ INFO_BOT_TOKEN не найден в .env файле!")
        return
    
    logger.info("🤖 Запуск информационного бота...")
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("contact", contact_command))
    
    logger.info("✅ Бот запущен и готов к работе!")
    
    application.run_polling()

if __name__ == '__main__':
    main()
