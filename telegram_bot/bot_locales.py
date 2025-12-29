"""
Локализация для Telegram бота
Translations for Telegram bot
"""

BOT_TRANSLATIONS = {
    "ru": {
        # Команды и меню
        "welcome": "👋 Привет, {username}!\n\n🛍 Добро пожаловать в бот управления товарами.\n\nВыберите действие из меню:",
        "access_denied": "❌ У вас нет доступа к этому боту.\nВаш ID: {user_id}\n\nПопросите администратора добавить ваш ID в список авторизованных пользователей.",
        
        # Кнопки главного меню
        "btn_add_product": "➕ Добавить товар",
        "btn_delete_product": "🗑 Удалить товар",
        "btn_list_products": "📋 Список товаров",
        "btn_categories": "📁 Категории",
        "btn_cancel": "❌ Отмена",
        "btn_done": "✅ Готово",
        "btn_skip": "⏭ Пропустить",
        "btn_skip_no_photo": "⏭ Пропустить (без фото)",
        "btn_add": "➕ Добавить",
        
        # Добавление товара
        "enter_product_name": "📝 Введите название товара:",
        "enter_description": "📝 Введите описание товара:",
        "enter_price": "💰 Введите цену товара (в сумах, только число):",
        "price_error": "❌ Ошибка! Введите цену числом (например: 50000)",
        "select_category": "📁 Выберите категорию:",
        "category_error": "❌ Неверная категория. Выберите из предложенных кнопок.",
        
        # Фотографии
        "send_photos": "📸 Отправьте фотографии товара (до 9 штук).\n\nОтправляйте по одному фото.\nПосле загрузки всех фото нажмите '✅ Готово'\n\nИли нажмите '⏭ Пропустить' чтобы добавить товар без изображений.",
        "photo_uploading": "⏳ Загружаю фото {current}/9...",
        "photo_uploaded": "✅ Фото {current}/9 загружено успешно!\n\nОтправьте еще фото или нажмите '✅ Готово'",
        "photo_limit": "⚠️ Достигнут лимит в 9 фотографий.\nНажмите '✅ Готово' чтобы завершить добавление товара.",
        "photo_error": "❌ Ошибка загрузки фото. Попробуйте еще раз.",
        
        # Цвета
        "select_colors": "🎨 <b>Выберите доступные цвета товара</b>\n\nНажимайте на кнопки, чтобы добавить цвет.\nКогда закончите, нажмите '✅ Готово'",
        "colors_skipped": "⏭ Цвета пропущены",
        "colors_selected": "✅ Выбрано цветов: {count}",
        "color_added": "✅ Цвет добавлен",
        "color_removed": "❌ Цвет убран",
        
        # Характеристики
        "enter_attr_name": "📝 Введите название первой характеристики:\n\nИли нажмите '⏭ Пропустить' чтобы завершить без характеристик",
        "enter_attr_values": "📝 Введите варианты для характеристики '<b>{attr_name}</b>':\n\nОтправляйте по одному варианту.\nКогда закончите, нажмите '✅ Готово'",
        "attr_value_added": "✅ Вариант добавлен: <b>{value}</b>\nВсего вариантов: {count}\n\nПродолжайте вводить варианты или нажмите '✅ Готово'",
        "attr_value_required": "⚠️ Добавьте хотя бы один вариант!",
        "attr_first_done": "✅ Первая характеристика добавлена!\n\nХотите добавить вторую характеристику?",
        "enter_attr2_name": "📝 Введите название второй характеристики:",
        
        # Сохранение товара
        "product_saved": "✅ <b>Товар успешно добавлен!</b>\n\n📦 Название: {name}\n📝 Описание: {description}\n💰 Цена: {price:,} сум\n📁 Категория: {category}\n📸 Фотографий: {photos}\n🎨 Цветов: {colors}\n📋 Характеристик: {attrs}\n🆔 ID: <code>{id}</code>",
        "product_save_error": "❌ Ошибка при добавлении товара в базу данных.",
        
        # Удаление товара
        "select_product_to_delete": "🗑 <b>Выберите товар для удаления:</b>\n\nВсего товаров: {count}",
        "no_products": "📭 Товаров пока нет в базе данных.",
        "product_deleted": "✅ <b>Товар успешно удален:</b>\n\n📦 {name}\n💰 {price:,} сум\n🆔 {id}",
        "product_not_found": "❌ Товар не найден",
        "delete_error": "❌ Ошибка удаления",
        
        # Список товаров
        "products_list": "📋 <b>Список товаров ({count}):</b>\n\n",
        "product_item": "{num}. <b>{name}</b>\n   💰 Цена: {price:,} сум\n   🆔 ID: <code>{id}</code>\n\n",
        "products_more": "\n... и еще {count} товаров",
        
        # Категории
        "categories_list": "📁 <b>Категории товаров:</b>\n\n",
        "category_item": "<b>{name}</b>\n   🆔 ID: <code>{id}</code>\n\n",
        "no_categories": "📭 Категории не настроены в конфигурации.",
        
        # Общие сообщения
        "operation_cancelled": "❌ Операция отменена.",
        "access_forbidden": "❌ Доступ запрещен",
    },
    
    "en": {
        # Commands and menu
        "welcome": "👋 Hello, {username}!\n\n🛍 Welcome to the product management bot.\n\nSelect an action from the menu:",
        "access_denied": "❌ You don't have access to this bot.\nYour ID: {user_id}\n\nAsk the administrator to add your ID to the authorized users list.",
        
        # Main menu buttons
        "btn_add_product": "➕ Add Product",
        "btn_delete_product": "🗑 Delete Product",
        "btn_list_products": "📋 Product List",
        "btn_categories": "📁 Categories",
        "btn_cancel": "❌ Cancel",
        "btn_done": "✅ Done",
        "btn_skip": "⏭ Skip",
        "btn_skip_no_photo": "⏭ Skip (no photo)",
        "btn_add": "➕ Add",
        
        # Adding product
        "enter_product_name": "📝 Enter product name:",
        "enter_description": "📝 Enter product description:",
        "enter_price": "💰 Enter product price (in UZS, numbers only):",
        "price_error": "❌ Error! Enter price as a number (e.g., 50000)",
        "select_category": "📁 Select category:",
        "category_error": "❌ Invalid category. Choose from the suggested buttons.",
        
        # Photos
        "send_photos": "📸 Send product photos (up to 9).\n\nSend one photo at a time.\nAfter uploading all photos, press '✅ Done'\n\nOr press '⏭ Skip' to add product without images.",
        "photo_uploading": "⏳ Uploading photo {current}/9...",
        "photo_uploaded": "✅ Photo {current}/9 uploaded successfully!\n\nSend more photos or press '✅ Done'",
        "photo_limit": "⚠️ Reached limit of 9 photos.\nPress '✅ Done' to finish adding product.",
        "photo_error": "❌ Photo upload error. Try again.",
        
        # Colors
        "select_colors": "🎨 <b>Select available product colors</b>\n\nClick buttons to add color.\nWhen finished, press '✅ Done'",
        "colors_skipped": "⏭ Colors skipped",
        "colors_selected": "✅ Colors selected: {count}",
        "color_added": "✅ Color added",
        "color_removed": "❌ Color removed",
        
        # Attributes
        "enter_attr_name": "📝 Enter first attribute name:\n\nOr press '⏭ Skip' to finish without attributes",
        "enter_attr_values": "📝 Enter options for attribute '<b>{attr_name}</b>':\n\nSend one option at a time.\nWhen finished, press '✅ Done'",
        "attr_value_added": "✅ Option added: <b>{value}</b>\nTotal options: {count}\n\nContinue entering options or press '✅ Done'",
        "attr_value_required": "⚠️ Add at least one option!",
        "attr_first_done": "✅ First attribute added!\n\nWould you like to add a second attribute?",
        "enter_attr2_name": "📝 Enter second attribute name:",
        
        # Saving product
        "product_saved": "✅ <b>Product added successfully!</b>\n\n📦 Name: {name}\n📝 Description: {description}\n💰 Price: {price:,} UZS\n📁 Category: {category}\n📸 Photos: {photos}\n🎨 Colors: {colors}\n📋 Attributes: {attrs}\n🆔 ID: <code>{id}</code>",
        "product_save_error": "❌ Error adding product to database.",
        
        # Deleting product
        "select_product_to_delete": "🗑 <b>Select product to delete:</b>\n\nTotal products: {count}",
        "no_products": "📭 No products in database yet.",
        "product_deleted": "✅ <b>Product deleted successfully:</b>\n\n📦 {name}\n💰 {price:,} UZS\n🆔 {id}",
        "product_not_found": "❌ Product not found",
        "delete_error": "❌ Delete error",
        
        # Product list
        "products_list": "📋 <b>Product List ({count}):</b>\n\n",
        "product_item": "{num}. <b>{name}</b>\n   💰 Price: {price:,} UZS\n   🆔 ID: <code>{id}</code>\n\n",
        "products_more": "\n... and {count} more products",
        
        # Categories
        "categories_list": "📁 <b>Product Categories:</b>\n\n",
        "category_item": "<b>{name}</b>\n   🆔 ID: <code>{id}</code>\n\n",
        "no_categories": "📭 Categories not configured.",
        
        # General messages
        "operation_cancelled": "❌ Operation cancelled.",
        "access_forbidden": "❌ Access forbidden",
    }
}


def get_bot_translation(key: str, language: str = "ru", **kwargs) -> str:
    """
    Получить перевод для бота с форматированием
    Get bot translation with formatting
    
    Args:
        key: Ключ перевода / Translation key
        language: Код языка (ru, en) / Language code
        **kwargs: Параметры для форматирования / Formatting parameters
        
    Returns:
        Переведенная строка / Translated string
    """
    if language not in BOT_TRANSLATIONS:
        language = "ru"
    
    text = BOT_TRANSLATIONS[language].get(key, key)
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    
    return text


def get_all_bot_translations(language: str = "ru") -> dict:
    """
    Получить все переводы бота для языка
    Get all bot translations for a language
    
    Args:
        language: Код языка / Language code
        
    Returns:
        Словарь переводов / Dictionary of translations
    """
    if language not in BOT_TRANSLATIONS:
        language = "ru"
    
    return BOT_TRANSLATIONS[language]
