"""
AI Database Helper - модуль для работы с базой данных товаров
Используется AI ботом для получения информации о товарах
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json


def get_db_connection():
    """Подключение к PostgreSQL базе данных"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Проверка на удаленную БД (Neon, AWS)
        if 'neon.tech' in database_url or 'amazonaws.com' in database_url:
            if 'sslmode=' not in database_url:
                database_url = database_url + ('&' if '?' in database_url else '?') + 'sslmode=require'
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        # Локальное подключение
        conn = psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('PGUSER', 'postgres'),
            password=os.getenv('PGPASSWORD', ''),
            database=os.getenv('PGDATABASE', 'shop_db'),
            cursor_factory=RealDictCursor
        )
    return conn


def get_all_products_info():
    """
    Получить информацию о всех товарах с деталями
    
    Returns:
        list: Список товаров с полной информацией
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Получаем товары с категориями
        cur.execute('''
            SELECT 
                p.id,
                p.name,
                p.description,
                p.price,
                p.colors,
                p.attributes,
                p.category_id,
                c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.name
        ''')
        
        products = cur.fetchall()
        
        # Для каждого товара получаем информацию о наличии
        for product in products:
            product_id = product['id']
            
            # Получаем информацию о наличии из inventory
            cur.execute('''
                SELECT 
                    color,
                    attribute1_value,
                    attribute2_value,
                    quantity
                FROM product_inventory
                WHERE product_id = %s AND quantity > 0
            ''', (product_id,))
            
            inventory = cur.fetchall()
            product['inventory'] = inventory
        
        cur.close()
        conn.close()
        
        return products
    except Exception as e:
        print(f"❌ Ошибка получения товаров: {e}")
        return []


def search_products(query):
    """
    Поиск товаров по ключевым словам
    
    Args:
        query (str): Поисковый запрос
        
    Returns:
        list: Найденные товары
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Разбиваем запрос на слова и убираем "мусор"
        stop_words = {'есть', 'ли', 'у', 'вас', 'цена', 'сколько', 'стоит', 'покажи', 'найди', 'хочу', 'купить', 'привет', 'mona', 'мона'}
        keywords = [word for word in query.lower().split() if word not in stop_words and len(word) > 2]
        
        if not keywords:
            # Если после очистки ничего не осталось, ищем по оригиналу (на всякий случай)
            keywords = [query.lower()]

        # Формируем динамический SQL запрос для поиска по любому из ключевых слов
        sql_query = '''
            SELECT DISTINCT
                p.id,
                p.name,
                p.description,
                p.price,
                p.colors,
                p.attributes,
                p.category_id,
                c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE 
        '''
        
        conditions = []
        params = []
        
        for word in keywords:
            conditions.append("(LOWER(p.name) LIKE %s OR LOWER(p.description) LIKE %s OR LOWER(c.name) LIKE %s)")
            pattern = f'%{word}%'
            params.extend([pattern, pattern, pattern])
            
        if conditions:
            sql_query += " OR ".join(conditions)
        else:
            # Fallback
            sql_query += " LOWER(p.name) LIKE %s "
            params = [f'%{query}%']

        sql_query += ' ORDER BY p.name LIMIT 5' # Ограничиваем выдачу

        cur.execute(sql_query, tuple(params))
        products = cur.fetchall()
        
        # Добавляем информацию о наличии
        for product in products:
            cur.execute('''
                SELECT color, attribute1_value, attribute2_value, quantity
                FROM product_inventory
                WHERE product_id = %s
            ''', (product['id'],))
            product['inventory'] = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return products
    except Exception as e:
        print(f"❌ Ошибка поиска товаров: {e}")
        return []


def get_product_details(product_id):
    """
    Получить детальную информацию о товаре
    
    Args:
        product_id (str): ID товара
        
    Returns:
        dict: Информация о товаре или None
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute('''
            SELECT 
                p.id,
                p.name,
                p.description,
                p.price,
                p.colors,
                p.attributes,
                p.category_id,
                c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.id = %s
        ''', (product_id,))
        
        product = cur.fetchone()
        
        if product:
            # Получаем наличие
            cur.execute('''
                SELECT color, attribute1_value, attribute2_value, quantity
                FROM product_inventory
                WHERE product_id = %s
            ''', (product_id,))
            product['inventory'] = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return product
    except Exception as e:
        print(f"❌ Ошибка получения товара: {e}")
        return None


def format_products_for_ai(products):
    """
    Форматирует список товаров в текст для AI
    
    Args:
        products (list): Список товаров
        
    Returns:
        str: Отформатированный текст
    """
    if not products:
        return "В базе данных нет товаров."
    
    context = "ТОВАРЫ В МАГАЗИНЕ:\n\n"
    
    for idx, product in enumerate(products, 1):
        context += f"{idx}. {product['name']}\n"
        context += f"   Ссылка: https://monvoir.shop/product/{product['id']}\n"
        context += f"   Цена: {product['price']:,} сум\n"
        
        if product.get('description'):
            context += f"   Описание: {product['description']}\n"
        
        if product.get('category_name'):
            context += f"   Категория: {product['category_name']}\n"
        
        # Цвета
        if product.get('colors'):
            colors = ', '.join(product['colors'])
            context += f"   Доступные цвета: {colors}\n"
        
        # Атрибуты (размеры и т.д.)
        if product.get('attributes'):
            attrs = product['attributes']
            if isinstance(attrs, str):
                attrs = json.loads(attrs)
            
            for attr in attrs:
                attr_name = attr.get('name', 'Характеристика')
                attr_values = ', '.join(attr.get('values', []))
                context += f"   {attr_name}: {attr_values}\n"
        
        # Наличие
        inventory = product.get('inventory', [])
        if inventory:
            # Фильтруем только те варианты, где quantity > 0
            available_items = [item for item in inventory if item['quantity'] > 0]
            
            if available_items:
                context += f"   В наличии:\n"
                for item in available_items:
                    parts = []
                    if item.get('color'):
                        parts.append(f"цвет {item['color']}")
                    if item.get('attribute1_value'):
                        parts.append(item['attribute1_value'])
                    if item.get('attribute2_value'):
                        parts.append(item['attribute2_value'])
                    
                    variant = ', '.join(parts) if parts else 'стандартный'
                    # НЕ показываем цифры даже боту, чтобы он случайно не проговорился
                    context += f"      - {variant}: Есть в наличии\n"
            else:
                context += f"   Статус: Нет в наличии (раскуплен)\n"
        else:
            context += f"   Статус: Нет в наличии\n"
            
    return context



def get_categories():
    """Получить список всех категорий"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('SELECT id, name FROM categories ORDER BY sort_order, name')
        categories = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return categories
    except Exception as e:
        print(f"❌ Ошибка получения категорий: {e}")
        return []


def get_order_status(order_id):
    """
    Получить статус заказа по ID
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Проверяем, существует ли таблица orders
        cur.execute("SELECT to_regclass('public.orders')")
        if not cur.fetchone()['to_regclass']:
            cur.close()
            conn.close()
            return "Сайт пока не поддерживает отслеживание заказов через бота."
            
        # Создаем новый курсор для второго запроса
        cur = conn.cursor()
        
        # Используем поиск по подстроке (но только с начала строки)
        cur.execute('''
            SELECT id, status, total, created_at, delivery_address, customer_name, customer_phone, payment_method
            FROM orders
            WHERE id::text ILIKE %s
        ''', (f'{order_id}%',))

        order = cur.fetchone()

        if order:
            # Получаем состав заказа
            cur.execute('''
                SELECT name, quantity, price, selected_color, selected_attributes
                FROM order_items
                WHERE order_id = %s
            ''', (order['id'],))
            items = cur.fetchall()
            
            cur.close()
            conn.close()

            status_map = {
                'pending': 'Ожидает оплаты',
                'processing': 'В обработке',
                'shipped': 'Отправлен',
                'delivered': 'Доставлен',
                'cancelled': 'Отменен',
                'paid': 'Оплачен',
                'reviewing': 'На проверке'
            }
            status_text = status_map.get(order['status'], order['status'])
            
            # Формируем детальный отчет
            details = f"📦 ЗАКАЗ #{order['id']}\n"
            details += f"🗓 Дата: {order['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            details += f"🔄 Статус: {status_text}\n"
            details += f"💰 Сумма: {order.get('total', 0):,} сум\n"
            details += f"💳 Оплата: {order.get('payment_method', 'Не указано')}\n"
            
            if order.get('delivery_address'):
                details += f"📍 Адрес доставки: {order['delivery_address']}\n"
            if order.get('customer_name'):
                details += f"👤 Клиент: {order['customer_name']} ({order.get('customer_phone', '')})\n"
            
            details += "\n🛒 СОСТАВ ЗАКАЗА:\n"
            for item in items:
                item_desc = f"- {item['name']} (x{item['quantity']})"
                if item.get('selected_color'):
                    item_desc += f", Цвет: {item['selected_color']}"
                if item.get('selected_attributes'):
                    # Пробуем распарсить JSON если это строка
                    attrs = item['selected_attributes']
                    if isinstance(attrs, str):
                        try:
                            attrs = json.loads(attrs)
                        except:
                            pass
                    # Если словарь
                    if isinstance(attrs, dict):
                        size = attrs.get('Размер') or attrs.get('Size')
                        if size:
                            item_desc += f", Р-р: {size}"
                
                details += f"{item_desc}\n"
                
            return details
        else:
            cur.close()
            conn.close()
            return None
            
    except Exception as e:
        print(f"❌ Ошибка проверки заказа: {e}")
        return None
