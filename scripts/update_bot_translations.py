"""
Скрипт для автоматического обновления telegrambot.py с переводами
Script to automatically update telegrambot.py with translations
"""

import re

# Маппинг хардкодных строк на ключи переводов
# Mapping of hardcoded strings to translation keys
REPLACEMENTS = {
    # Buttons and menu
    r'"➕ Добавить товар"': 'self.t("btn_add_product")',
    r'"🗑 Удалить товар"': 'self.t("btn_delete_product")',
    r'"📋 Список товаров"': 'self.t("btn_list_products")',
    r'"📁 Категории"': 'self.t("btn_categories")',
    r'"❌ Отмена"': 'self.t("btn_cancel")',
    r'"✅ Готово"': 'self.t("btn_done")',
    r'"⏭ Пропустить"': 'self.t("btn_skip")',
    r'"⏭ Пропустить \(без фото\)"': 'self.t("btn_skip_no_photo")',
    r'"➕ Добавить"': 'self.t("btn_add")',
    
    # Messages
    r'"❌ Доступ запрещен"': 'self.t("access_forbidden")',
    r'"📝 Введите название товара:"': 'self.t("enter_product_name")',
    r'"📝 Введите описание товара:"': 'self.t("enter_description")',
    r'"💰 Введите цену товара \(в сумах, только число\):"': 'self.t("enter_price")',
    r'"❌ Ошибка! Введите цену числом \(например: 50000\)"': 'self.t("price_error")',
    r'"📁 Выберите категорию:"': 'self.t("select_category")',
    r'"❌ Неверная категория\. Выберите из предложенных кнопок\."': 'self.t("category_error")',
    r'"❌ Операция отменена\."': 'self.t("operation_cancelled")',
    r'"📭 Товаров пока нет в базе данных\."': 'self.t("no_products")',
    r'"📭 Категории не настроены в конфигурации\."': 'self.t("no_categories")',
    r'"❌ Товар не найден"': 'self.t("product_not_found")',
    r'"❌ Ошибка удаления"': 'self.t("delete_error")',
    r'"❌ Ошибка загрузки фото\. Попробуйте еще раз\."': 'self.t("photo_error")',
}

def update_telegrambot():
    """Update telegrambot.py with translations"""
    
    # Read the file
    file_path = 'telegram_bot/telegrambot.py'
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        # Fallback for old location
        file_path = 'telegrambot.py'
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    
    # Apply replacements
    for pattern, replacement in REPLACEMENTS.items():
        content = re.sub(pattern, replacement, content)
    
    # Write back
    with open('telegrambot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ telegrambot.py updated with translations")

if __name__ == "__main__":
    update_telegrambot()
