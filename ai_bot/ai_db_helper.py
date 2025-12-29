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
        
        search_pattern = f'%{query.lower()}%'
        
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
            WHERE LOWER(p.name) LIKE %s 
               OR LOWER(p.description) LIKE %s
               OR LOWER(c.name) LIKE %s
            ORDER BY p.name
        ''', (search_pattern, search_pattern, search_pattern))
        
        products = cur.fetchall()
        
        # Добавляем информацию о наличии
        for product in products:
            cur.execute('''
                SELECT color, attribute1_value, attribute2_value, quantity
                FROM product_inventory
                WHERE product_id = %s AND quantity > 0
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
        cur = conn.cursor()
        
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
            context += f"   В наличии:\n"
            for item in inventory:
                parts = []
                if item.get('color'):
                    parts.append(f"цвет {item['color']}")
                if item.get('attribute1_value'):
                    parts.append(item['attribute1_value'])
                if item.get('attribute2_value'):
                    parts.append(item['attribute2_value'])
                
                variant = ', '.join(parts) if parts else 'стандартный'
                context += f"      - {variant}: {item['quantity']} шт\n"
        else:
            context += f"   Наличие: уточняйте у менеджера\n"
        
        context += "\n"
    
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
        
        # Используем поиск по подстроке для поддержки и полных UUID и коротких ID
        cur.execute('''
            SELECT status, total, created_at 
            FROM orders 
            WHERE id::text ILIKE %s
        ''', (f'%{order_id}%',))
        
        order = cur.fetchone()
        cur.close()
        conn.close()
        
        if order:
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
            return f"ID заказа: {order_id}\nСтатус: {status_text}\nСумма: {order.get('total', 0):,} сум"
        else:
            return None
            
    except Exception as e:
        print(f"❌ Ошибка проверки заказа: {e}")
        return None
