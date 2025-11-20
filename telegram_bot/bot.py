"""
Telegram бот для управления товарами в магазине
Автономная версия - работает независимо от основного проекта
"""

import os
import json
import telebot
from telebot import types
import cloudinary
import cloudinary.uploader
import requests
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
import time
from typing import Dict, Any, List, Optional, cast

load_dotenv()
from db_operations import (
    add_product, 
    delete_product, 
    get_all_products,
    get_product_by_id,
    get_categories_from_config,
    find_products_by_name
)


class ProductBot:
    """Класс для управления Telegram ботом товаров"""
    
    def __init__(self, token):
        """
        Инициализация бота
        
        Args:
            token (str): Telegram Bot API токен
        """
        self.bot = telebot.TeleBot(token)
        self.authorized_users = self._load_authorized_users()
        self.user_states = {}  # Хранение состояний пользователей
        self.temp_data = {}    # Временные данные для создания товаров
        
        # Настройка Cloudinary
        self._setup_cloudinary()
        
        # Регистрация обработчиков
        self._register_handlers()
    
    def _setup_cloudinary(self):
        """Настраивает Cloudinary используя переменные окружения"""
        try:
            cloudinary.config(
                cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
                api_key=os.getenv('CLOUDINARY_API_KEY'),
                api_secret=os.getenv('CLOUDINARY_API_SECRET')
            )
            print("✅ Cloudinary настроен успешно")
        except Exception as e:
            print(f"⚠️ Ошибка настройки Cloudinary: {e}")
    
    def _upload_photo_to_cloudinary(self, file_id):
        """
        Загружает фото из Telegram в Cloudinary
        
        Args:
            file_id (str): Telegram file ID
            
        Returns:
            str: URL загруженного изображения или None при ошибке
        """
        try:
            # Получаем информацию о файле
            file_info = self.bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{self.bot.token}/{file_info.file_path}"
            
            # Скачиваем файл
            response = requests.get(file_url)
            if response.status_code != 200:
                print(f"❌ Ошибка скачивания фото: {response.status_code}")
                return None
            
            # Загружаем в Cloudinary
            upload_result = cloudinary.uploader.upload(
                BytesIO(response.content),
                folder="telegram_shop_products"
            )
            
            return upload_result.get('secure_url')
        except Exception as e:
            print(f"❌ Ошибка загрузки в Cloudinary: {e}")
            return None
    
    def _load_authorized_users(self):
        """Загружает список авторизованных пользователей из settingsbot.json"""
        try:
            config_path = Path(__file__).parent / 'settingsbot.json'
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('authorized_users', []))
        except FileNotFoundError:
            print("⚠️ Файл settingsbot.json не найден. Создайте его с списком авторизованных пользователей.")
            return set()
        except Exception as e:
            print(f"❌ Ошибка загрузки авторизованных пользователей: {e}")
            return set()
    
    def _is_authorized(self, user_id):
        """
        Проверяет, авторизован ли пользователь
        
        Args:
            user_id (int): Telegram ID пользователя
            
        Returns:
            bool: True если авторизован
        """
        return user_id in self.authorized_users
    
    def _create_main_menu(self):
        """Создает главное меню с кнопками"""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn_add = types.KeyboardButton("➕ Добавить товар")
        btn_delete = types.KeyboardButton("🗑 Удалить товар")
        btn_list = types.KeyboardButton("📋 Список товаров")
        btn_categories = types.KeyboardButton("📁 Категории")
        markup.add(btn_add, btn_delete)
        markup.add(btn_list, btn_categories)
        return markup
    
    def _register_handlers(self):
        """Регистрирует все обработчики команд и сообщений"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            user_id = message.from_user.id
            
            if not self._is_authorized(user_id):
                self.bot.send_message(
                    message.chat.id,
                    "❌ У вас нет доступа к этому боту.\n"
                    f"Ваш ID: {user_id}\n\n"
                    "Попросите администратора добавить ваш ID в список авторизованных пользователей."
                )
                return
            
            username = message.from_user.username or message.from_user.first_name
            self.bot.send_message(
                message.chat.id,
                f"👋 Привет, {username}!\n\n"
                "🛍 Добро пожаловать в бот управления товарами.\n\n"
                "Выберите действие из меню:",
                reply_markup=self._create_main_menu()
            )
        
        @self.bot.message_handler(func=lambda message: message.text == "➕ Добавить товар")
        def handle_add_product(message):
            if not self._is_authorized(message.from_user.id):
                self.bot.send_message(message.chat.id, "❌ Доступ запрещен")
                return
            
            self.user_states[message.from_user.id] = "awaiting_product_name"
            self.temp_data[message.from_user.id] = {}
            
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("❌ Отмена"))
            
            self.bot.send_message(
                message.chat.id,
                "📝 Введите название товара:",
                reply_markup=markup
            )
        
        @self.bot.message_handler(func=lambda message: message.text == "🗑 Удалить товар")
        def handle_delete_product_menu(message):
            if not self._is_authorized(message.from_user.id):
                self.bot.send_message(message.chat.id, "❌ Доступ запрещен")
                return
            
            # Получаем все товары
            products = get_all_products()
            
            if not products:
                self.bot.send_message(
                    message.chat.id,
                    "📭 Товаров пока нет в базе данных.",
                    reply_markup=self._create_main_menu()
                )
                return
            
            # Создаем inline кнопки для каждого товара
            markup = types.InlineKeyboardMarkup(row_width=1)
            for product in products[:20]:  # Показываем первые 20
                p = cast(Dict[str, Any], product)
                btn_text = f"🗑 {p['name']} - {p['price']:,} сум"
                callback_data = f"delete_{p['id']}"
                markup.add(types.InlineKeyboardButton(btn_text, callback_data=callback_data))
            
            self.bot.send_message(
                message.chat.id,
                "🗑 <b>Выберите товар для удаления:</b>\n\n"
                f"Всего товаров: {len(products)}",
                parse_mode='HTML',
                reply_markup=markup
            )
        
        @self.bot.message_handler(func=lambda message: message.text == "📋 Список товаров")
        def handle_list_products(message):
            if not self._is_authorized(message.from_user.id):
                self.bot.send_message(message.chat.id, "❌ Доступ запрещен")
                return
            
            products = get_all_products()
            
            if not products:
                self.bot.send_message(
                    message.chat.id,
                    "📭 Товаров пока нет в базе данных."
                )
                return
            
            response = f"📋 <b>Список товаров ({len(products)}):</b>\n\n"
            
            for idx, product in enumerate(products[:30], 1):  # Показываем первые 30
                p = cast(Dict[str, Any], product)
                response += f"{idx}. <b>{p['name']}</b>\n"
                response += f"   💰 Цена: {p['price']:,} сум\n"
                response += f"   🆔 ID: <code>{p['id']}</code>\n\n"
            
            if len(products) > 30:
                response += f"\n... и еще {len(products) - 30} товаров"
            
            self.bot.send_message(
                message.chat.id,
                response,
                parse_mode='HTML'
            )
        
        @self.bot.message_handler(func=lambda message: message.text == "📁 Категории")
        def handle_categories(message):
            if not self._is_authorized(message.from_user.id):
                self.bot.send_message(message.chat.id, "❌ Доступ запрещен")
                return
            
            categories = get_categories_from_config()
            
            if not categories:
                self.bot.send_message(
                    message.chat.id,
                    "📭 Категории не настроены в конфигурации."
                )
                return
            
            response = "📁 <b>Категории товаров:</b>\n\n"
            
            for cat in categories:
                response += f"<b>{cat['name']}</b>\n"
                response += f"   🆔 ID: <code>{cat['id']}</code>\n\n"
            
            self.bot.send_message(
                message.chat.id,
                response,
                parse_mode='HTML'
            )
        
        @self.bot.message_handler(func=lambda message: message.text == "❌ Отмена")
        def handle_cancel(message):
            user_id = message.from_user.id
            
            if user_id in self.user_states:
                del self.user_states[user_id]
            if user_id in self.temp_data:
                del self.temp_data[user_id]
            
            self.bot.send_message(
                message.chat.id,
                "❌ Операция отменена.",
                reply_markup=self._create_main_menu()
            )
        
        @self.bot.callback_query_handler(func=lambda call: call.data.startswith('delete_'))
        def handle_delete_callback(call):
            """Обработка удаления товара"""
            if not self._is_authorized(call.from_user.id):
                self.bot.answer_callback_query(call.id, "❌ Доступ запрещен")
                return
            
            product_id = call.data.replace('delete_', '')
            
            # Получаем информацию о товаре перед удалением
            product = get_product_by_id(product_id)
            
            if not product:
                self.bot.answer_callback_query(call.id, "❌ Товар не найден")
                return
            
            # Удаляем товар
            if delete_product(product_id):
                self.bot.answer_callback_query(call.id, "✅ Товар удален")
                p = cast(Dict[str, Any], product)
                self.bot.edit_message_text(
                    f"✅ <b>Товар успешно удален:</b>\n\n"
                    f"📦 {p['name']}\n"
                    f"💰 {p['price']:,} сум\n"
                    f"🆔 {product_id}",
                    call.message.chat.id,
                    call.message.message_id,
                    parse_mode='HTML'
                )
            else:
                self.bot.answer_callback_query(call.id, "❌ Ошибка удаления")
        
        # Обработчик фотографий
        @self.bot.message_handler(content_types=['photo'])
        def handle_photo(message):
            """Обработка получения фото от пользователя"""
            user_id = message.from_user.id
            
            if not self._is_authorized(user_id):
                self.bot.send_message(message.chat.id, "❌ Доступ запрещен")
                return
            
            # Проверяем, находится ли пользователь в состоянии ожидания фото
            user_state = self.user_states.get(user_id)
            if user_state != "awaiting_images":
                return
            
            # Проверяем лимит фото (безопасно через .get())
            user_temp = self.temp_data.get(user_id)
            if not user_temp:
                return
            
            current_images = user_temp.get('images', [])
            if len(current_images) >= 9:
                self.bot.send_message(
                    message.chat.id,
                    "⚠️ Достигнут лимит в 9 фотографий.\n"
                    "Нажмите '✅ Готово' чтобы завершить добавление товара."
                )
                return
            
            # Получаем самое большое фото
            photo = message.photo[-1]
            
            # Отправляем статус загрузки
            status_msg = self.bot.send_message(
                message.chat.id,
                f"⏳ Загружаю фото {len(current_images) + 1}/9..."
            )
            
            # Загружаем фото в Cloudinary
            photo_url = self._upload_photo_to_cloudinary(photo.file_id)
            
            # Повторно проверяем состояние после загрузки
            # (могли нажать "Готово" или "Отмена" пока фото загружалось)
            user_temp_after = self.temp_data.get(user_id)
            user_state_after = self.user_states.get(user_id)
            
            if not user_temp_after or user_state_after != "awaiting_images":
                # Пользователь уже завершил процесс, игнорируем результат загрузки
                try:
                    self.bot.delete_message(message.chat.id, status_msg.message_id)
                except:
                    pass
                return
            
            if photo_url:
                # Добавляем URL в список (безопасно, т.к. проверили выше)
                user_temp_after['images'].append(photo_url)
                
                self.bot.edit_message_text(
                    f"✅ Фото {len(user_temp_after['images'])}/9 загружено успешно!\n\n"
                    f"Отправьте еще фото или нажмите '✅ Готово'",
                    message.chat.id,
                    status_msg.message_id
                )
            else:
                self.bot.edit_message_text(
                    "❌ Ошибка загрузки фото. Попробуйте еще раз.",
                    message.chat.id,
                    status_msg.message_id
                )
        
        # Обработчик состояний для добавления товара
        @self.bot.message_handler(func=lambda message: message.from_user.id in self.user_states)
        def handle_states(message):
            user_id = message.from_user.id
            state = self.user_states.get(user_id)
            
            if not state:
                return
            
            if state == "awaiting_product_name":
                # Сохраняем название
                self.temp_data[user_id]['name'] = message.text
                self.user_states[user_id] = "awaiting_description"
                
                self.bot.send_message(
                    message.chat.id,
                    "📝 Введите описание товара:"
                )
            
            elif state == "awaiting_description":
                # Сохраняем описание
                self.temp_data[user_id]['description'] = message.text
                self.user_states[user_id] = "awaiting_price"
                
                self.bot.send_message(
                    message.chat.id,
                    "💰 Введите цену товара (в сумах, только число):"
                )
            
            elif state == "awaiting_price":
                # Проверяем и сохраняем цену
                try:
                    price = int(message.text)
                    self.temp_data[user_id]['price'] = price
                    self.user_states[user_id] = "awaiting_category"
                    
                    # Показываем категории
                    categories = get_categories_from_config()
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
                    
                    for cat in categories:
                        markup.add(types.KeyboardButton(cat['name']))
                    markup.add(types.KeyboardButton("❌ Отмена"))
                    
                    self.bot.send_message(
                        message.chat.id,
                        "📁 Выберите категорию:",
                        reply_markup=markup
                    )
                except ValueError:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Ошибка! Введите цену числом (например: 50000)"
                    )
            
            elif state == "awaiting_category":
                # Находим выбранную категорию
                categories = get_categories_from_config()
                selected_category = None
                
                for cat in categories:
                    if cat['name'] == message.text:
                        selected_category = cat
                        break
                
                if not selected_category:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Неверная категория. Выберите из предложенных кнопок."
                    )
                    return
                
                self.temp_data[user_id]['category_id'] = selected_category['id']
                self.temp_data[user_id]['images'] = []  # Инициализируем список для фото
                self.user_states[user_id] = "awaiting_images"
                
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(types.KeyboardButton("✅ Готово"))
                markup.add(types.KeyboardButton("⏭ Пропустить (без фото)"))
                markup.add(types.KeyboardButton("❌ Отмена"))
                
                self.bot.send_message(
                    message.chat.id,
                    "📸 Отправьте фотографии товара (до 9 штук).\n\n"
                    "Отправляйте по одному фото.\n"
                    "После загрузки всех фото нажмите '✅ Готово'\n\n"
                    "Или нажмите '⏭ Пропустить' чтобы добавить товар без изображений.",
                    reply_markup=markup
                )
            
            elif state == "awaiting_images":
                if message.text == "⏭ Пропустить (без фото)":
                    images = ["https://via.placeholder.com/400x400?text=No+Image"]
                elif message.text == "✅ Готово":
                    images = self.temp_data[user_id].get('images', [])
                    if not images:
                        images = ["https://via.placeholder.com/400x400?text=No+Image"]
                else:
                    # Игнорируем текстовые сообщения в этом состоянии
                    return
                
                # Сохраняем товар в БД
                product = add_product(
                    name=self.temp_data[user_id]['name'],
                    description=self.temp_data[user_id]['description'],
                    price=self.temp_data[user_id]['price'],
                    images=images,
                    category_id=self.temp_data[user_id]['category_id']
                )
                
                if product:
                    p = cast(Dict[str, Any], product)
                    self.bot.send_message(
                        message.chat.id,
                        f"✅ <b>Товар успешно добавлен!</b>\n\n"
                        f"📦 Название: {p['name']}\n"
                        f"📝 Описание: {p['description']}\n"
                        f"💰 Цена: {p['price']:,} сум\n"
                        f"📁 Категория: {self.temp_data[user_id]['category_id']}\n"
                        f"📸 Фотографий: {len(images)}\n"
                        f"🆔 ID: <code>{p['id']}</code>",
                        parse_mode='HTML',
                        reply_markup=self._create_main_menu()
                    )
                else:
                    self.bot.send_message(
                        message.chat.id,
                        "❌ Ошибка при добавлении товара в базу данных.",
                        reply_markup=self._create_main_menu()
                    )
                
                # Очищаем состояние
                del self.user_states[user_id]
                del self.temp_data[user_id]
    
    def run(self):
        """Запускает бота в режиме polling с автоматическим переподключением"""
        print("🤖 Бот запущен и готов к работе...")
        print(f"👥 Авторизованных пользователей: {len(self.authorized_users)}")
        if self.authorized_users:
            print(f"   IDs: {list(self.authorized_users)}")
        else:
            print("   ⚠️ ВНИМАНИЕ: Список авторизованных пользователей пуст!")
            print("   Добавьте Telegram ID в файл settingsbot.json")
        
        retry_delay = 5
        max_retry_delay = 60
        
        while True:
            try:
                print("🔄 Подключение к Telegram...")
                self.bot.infinity_polling(timeout=60, long_polling_timeout=60)
            except (ConnectionError, Exception) as e:
                error_message = str(e)
                print(f"❌ Потеряно соединение с Telegram: {error_message}")
                print(f"⏳ Переподключение через {retry_delay} секунд...")
                time.sleep(retry_delay)
                
                retry_delay = min(retry_delay * 2, max_retry_delay)
                print("🔄 Попытка переподключения...")
            except KeyboardInterrupt:
                print("\n⛔ Бот остановлен пользователем")
                break


def main():
    """Главная функция запуска бота"""
    # Получаем токен из переменных окружения
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
        print("Установите переменную окружения TELEGRAM_BOT_TOKEN с токеном вашего бота.")
        return
    
    # Создаем и запускаем бота
    try:
        bot = ProductBot(bot_token)
        bot.run()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
