"""
AI Database Helper - модуль для работы с базой данных товаров
Используется AI ботом для получения информации о товарах
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
import re
from datetime import datetime, timedelta

# Кеш для результатов поиска товаров
_product_search_cache = {}
_cache_ttl = timedelta(seconds=60)  # Кеш на 60 секунд


def hex_to_color_name(hex_color):
    """
    Конвертирует HEX-код цвета в название на русском языке
    
    Args:
        hex_color (str): HEX-код цвета (например, #000000 или 000000)
        
    Returns:
        str: Название цвета на русском
    """
    # Убираем # если есть
    hex_color = hex_color.strip().lstrip('#').upper()
    
    # Словарь основных цветов
    color_map = {
        # Черные и серые
        '000000': 'черный',
        'FFFFFF': 'белый',
        '808080': 'серый',
        'C0C0C0': 'серебристый',
        '696969': 'темно-серый',
        'A9A9A9': 'светло-серый',
        '2F2F2F': 'темно-серый',
        'D3D3D3': 'светло-серый',
        
        # Красные
        'FF0000': 'красный',
        'DC143C': 'малиновый',
        'B22222': 'кирпично-красный',
        '8B0000': 'темно-красный',
        'FF6347': 'томатный',
        'FF4500': 'оранжево-красный',
        'FF1493': 'розовый',
        'FF69B4': 'ярко-розовый',
        'FFC0CB': 'светло-розовый',
        
        # Оранжевые
        'FFA500': 'оранжевый',
        'FF8C00': 'темно-оранжевый',
        'FF7F50': 'коралловый',
        
        # Желтые
        'FFFF00': 'желтый',
        'FFD700': 'золотой',
        'FFD700': 'золотистый',
        'FFFFE0': 'светло-желтый',
        'FFF8DC': 'кремовый',
        
        # Зеленые
        '008000': 'зеленый',
        '00FF00': 'лайм',
        '228B22': 'лесной зеленый',
        '32CD32': 'салатовый',
        '00FF7F': 'весенний зеленый',
        '2E8B57': 'морской зеленый',
        '006400': 'темно-зеленый',
        '00FF00': 'ярко-зеленый',
        'ADFF2F': 'желто-зеленый',
        
        # Синие
        '0000FF': 'синий',
        '000080': 'темно-синий',
        '00008B': 'навигационный синий',
        '191970': 'полночный синий',
        '4169E1': 'королевский синий',
        '1E90FF': 'ярко-синий',
        '00BFFF': 'небесно-голубой',
        '87CEEB': 'небесно-голубой',
        '4682B4': 'стальной синий',
        '708090': 'сланцево-серый',
        
        # Голубые и бирюзовые
        '00FFFF': 'голубой',
        '40E0D0': 'бирюзовый',
        '00CED1': 'темно-бирюзовый',
        '48D1CC': 'средне-бирюзовый',
        '20B2AA': 'светло-морской',
        
        # Фиолетовые
        '800080': 'фиолетовый',
        '4B0082': 'индиго',
        '9400D3': 'фиолетовый',
        '9932CC': 'темно-фиолетовый',
        'BA55D3': 'средне-фиолетовый',
        'DA70D6': 'орхидея',
        'EE82EE': 'фиолетовый',
        'DDA0DD': 'сливовый',
        'D8BFD8': 'чертополох',
        
        # Коричневые
        'A52A2A': 'коричневый',
        '8B4513': 'седло-коричневый',
        'CD853F': 'персиковый',
        'DEB887': 'беж',
        'F5DEB3': 'пшеничный',
        'D2B48C': 'загар',
        'BC8F8F': 'розово-коричневый',
        '800000': 'темно-коричневый',
        '654321': 'темно-коричневый',
    }
    
    # Проверяем точное совпадение
    if hex_color in color_map:
        return color_map[hex_color]
    
    # Если нет точного совпадения, пытаемся определить приблизительно
    if len(hex_color) == 6:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        
        # Определяем по RGB значениям
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        # Черный/серый
        if max_val < 50:
            return 'черный'
        if max_val < 128:
            return 'темно-серый'
        if diff < 30:
            if max_val > 200:
                return 'светло-серый'
            return 'серый'
        
        # Определяем основной цвет
        if r > g and r > b:
            if r > 200 and g < 100 and b < 100:
                return 'красный'
            elif r > 150:
                return 'оранжево-красный'
            return 'красно-коричневый'
        elif g > r and g > b:
            if g > 200 and r < 100 and b < 100:
                return 'зеленый'
            elif g > 150:
                return 'зелено-желтый'
            return 'темно-зеленый'
        elif b > r and b > g:
            if b > 200 and r < 100 and g < 100:
                return 'синий'
            elif b > 150:
                return 'голубой'
            return 'темно-синий'
        elif r > 150 and g > 150 and b < 100:
            return 'желтый'
        elif r > 150 and b > 150 and g < 100:
            return 'фиолетовый'
    
    # Если не удалось определить, возвращаем как есть (может быть уже название)
    return hex_color


def format_colors(colors):
    """
    Форматирует список цветов, конвертируя HEX-коды в названия
    
    Args:
        colors (list): Список цветов (могут быть HEX-коды или названия)
        
    Returns:
        str: Отформатированная строка с названиями цветов
    """
    if not colors:
        return ''
    
    color_names = []
    for color in colors:
        # Проверяем, является ли это HEX-кодом
        if isinstance(color, str) and re.match(r'^#?[0-9A-Fa-f]{6}$', color):
            color_names.append(hex_to_color_name(color))
        else:
            # Если это уже название, используем как есть
            color_names.append(str(color))
    
    return ', '.join(color_names)


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
            WHERE EXISTS (
                SELECT 1 FROM product_inventory pi 
                WHERE pi.product_id = p.id AND pi.quantity > 0
            )
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


def get_catalog_titles():
    """
    Получить только названия и ID всех товаров для анализа AI
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM products ORDER BY name")
        titles = cur.fetchall()
        cur.close()
        conn.close()
        return titles
    except Exception as e:
        print(f"❌ Ошибка получения каталога: {e}")
        return []


def search_products(query, include_out_of_stock=False):
    """
    Поиск товаров по ключевым словам
    
    Args:
        query (str): Поисковый запрос
        include_out_of_stock (bool): Включать ли товары, которых нет в наличии
        
    Returns:
        list: Найденные товары
    """
    try:
        norm_query = query.lower().strip()
        
        # Проверка кеша
        if norm_query in _product_search_cache:
            cache_data = _product_search_cache[norm_query]
            if datetime.now() < cache_data['expires']:
                return cache_data['products']
                
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Определяем, является ли запрос общим вопросом
        general_phrases = [
            'какие товары', 'что есть', 'что у вас', 'покажи все', 'какой ассортимент', 
            'что продаете', 'что в наличии', 'какие есть товары', 'все', 'каталог', 
            'ассортимент', 'товары', 'в наличии', 'shop', 'магазин', 'покажи товары'
        ]
        is_general = any(phrase == norm_query or phrase in norm_query for phrase in general_phrases)
        
        # Если общий запрос - возвращаем примеры из разных категорий
        if is_general:
            inventory_filter = "WHERE EXISTS (SELECT 1 FROM product_inventory pi WHERE pi.product_id = p.id AND pi.quantity > 0)" if not include_out_of_stock else ""
            cur.execute(f'''
                SELECT DISTINCT ON (p.category_id)
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
                {inventory_filter}
                ORDER BY p.category_id, p.name
                LIMIT 10
            ''')
            products = cur.fetchall()
        else:
            # Разбиваем запрос на слова и убираем "мусор"
            stop_words = {'есть', 'ли', 'у', 'вас', 'цена', 'сколько', 'стоит', 'покажи', 'найди', 'хочу', 'купить', 'привет', 'mona', 'мона', 'какие'}
            keywords = [word for word in norm_query.split() if word not in stop_words and len(word) > 2]
            
            if not keywords:
                # Если после очистки ничего не осталось, возвращаем пустой список
                cur.close()
                conn.close()
                return []

            # Формируем динамический SQL запрос для поиска по любому из ключевых слов
            inventory_clause = "(EXISTS (SELECT 1 FROM product_inventory pi WHERE pi.product_id = p.id AND pi.quantity > 0))" if not include_out_of_stock else "1=1"
            
            sql_query = f'''
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
                WHERE {inventory_clause} AND (
            '''
            
            conditions = []
            params = []
            
            for word in keywords:
                conditions.append("(LOWER(p.name) LIKE %s OR LOWER(p.description) LIKE %s OR LOWER(c.name) LIKE %s)")
                pattern = f'%{word}%'
                params.extend([pattern, pattern, pattern])
                
            if conditions:
                sql_query += "(" + " OR ".join(conditions) + "))"
            else:
                # Fallback
                sql_query += " LOWER(p.name) LIKE %s )"
                params = [f'%{query}%']

            sql_query += ' ORDER BY p.name LIMIT 10'  # Увеличиваем лимит для возможности показать больше

            cur.execute(sql_query, tuple(params))
            products = cur.fetchall()
        
        # Добавляем информацию о наличии (размеры/цвета) для каждого найденного товара
        if products:
            for product in products:
                cur.execute('''
                    SELECT color, attribute1_value, attribute2_value, quantity
                    FROM product_inventory
                    WHERE product_id = %s
                ''', (product['id'],))
                product['inventory'] = cur.fetchall()
        
        # Обновляем кеш
        _product_search_cache[norm_query] = {
            'products': products,
            'expires': datetime.now() + timedelta(minutes=5)
        }
        
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
    Форматирует список товаров в ТЕКСТ для AI (с описанием и всеми деталями)
    """
    if not products:
        return "[SYSTEM_REPORT: NO_PRODUCTS_FOUND_FOR_THIS_QUERY]"
    
    context = "=== DATABASE_RAW_DATA (FOR_INTERNAL_USE_ONLY) ===\n\n"
    
    for idx, product in enumerate(products, 1):
        context += f"PRODUCT_ENTRY_{idx}:\n"
        context += f"system_name: {product['name']}\n"
        context += f"db_price: {product['price']} сум\n"
        context += f"db_description: {product.get('description') or 'NULL_DATA'}\n"
        
        inventory = product.get('inventory', [])
        total_qty = 0
        if inventory:
            context += "INVENTORY_MATRIX:\n"
            for item in inventory:
                color = format_colors([item['color']]) if item.get('color') else "N/A"
                size = item.get('attribute1_value') or "N/A"
                qty = item.get('quantity', 0)
                total_qty += qty
                status = "IN_STOCK" if qty > 0 else "OUT_OF_STOCK"
                context += f"- VARIANT: [Color: {color}, Size: {size}] -> STATUS: {status} (Qty: {qty})\n"
        
        # Резюме для ИИ, чтобы он не гадал
        overall_status = "AVAILABLE_IN_STOCK" if total_qty > 0 else "OUT_OF_STOCK"
        context += f"TOTAL_STOCK_STATUS: {overall_status} (Total Qty: {total_qty})\n"
        
        if not inventory:
            context += "INVENTORY_STATUS: NO_DATA_FOUND (Contact manager to verify stock)\n"
        
        context += f"SYSTEM_UID_KEEP_SECRET: {product['id']}\n"
        context += "=== END_ENTRY ===\n\n"
            
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


def get_order_status(order_id, detailed=True, internal_raw=False):
    """
    Получить статус заказа по ID
    detailed: Если False, возвращает только статус и дату доставки (для краткого ответа)
    internal_raw: Если True, возвращает плоский текст для AI
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
            
        # 1. Поиск по началу ID (стандартный)
        cur.execute('''
            SELECT id, status, total, created_at, delivery_address, customer_name, customer_phone, payment_method,
                   has_backorder, backorder_delivery_date, estimated_delivery_days
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
                'pending': '⏳ Ожидает оплаты',
                'processing': '⚙️ В обработке',
                'shipped': '🚚 Отправлен',
                'delivered': '✅ Доставлен',
                'cancelled': '❌ Отменен',
                'paid': '💳 Оплачен',
                'reviewing': '🧐 На проверке'
            }
            status_text = status_map.get(order['status'], order['status'])
            created_at = order['created_at']

            # Если нужен плоский текст для AI
            if internal_raw:
                raw_info = f"ORDER_ID: {order['id']}\n"
                raw_info += f"STATUS: {order['status']} ({status_text})\n"
                raw_info += f"TOTAL: {order['total']} сум\n"
                raw_info += f"DATE: {created_at.strftime('%Y-%m-%d')}\n"
                raw_info += f"ITEMS: {len(items)} items\n"
                for i in items:
                    raw_info += f"- {i['name']} (x{i['quantity']}): {i['price']} сум, Color: {i['selected_color']}, Size: {i['selected_attributes']}\n"
                return raw_info

            # Формируем детальный отчет
            if order.get('backorder_delivery_date'):
                est_delivery = order['backorder_delivery_date']
            elif order.get('estimated_delivery_days'):
                est_delivery = created_at + timedelta(days=order['estimated_delivery_days'])
            else:
                est_delivery = created_at + timedelta(days=2)
            
            has_backorder = order.get('has_backorder', False)
            delivery_info = f"📅 <b>Доставка:</b> ~{est_delivery.strftime('%d.%m.%Y')}"
            if has_backorder:
                delivery_info += " <i>(под заказ)</i>"
            
            # ВСЕГДА ВОЗВРАЩАЕМ ПОЛНУЮ ИНФОРМАЦИЮ (для v4.7 клиента)
            full_msg = (
                f"🛍 <b>Заказ #{order['id'].split('-')[0].upper()}</b>\n"
                f"📅 <b>Дата:</b> {created_at.strftime('%d.%m.%Y')}\n"
                f"🔄 <b>Статус:</b> {status_text}\n"
                f"{delivery_info}\n"
                f"💳 <b>Оплата:</b> {order.get('payment_method', 'Карта/Наличные')}\n"
                f"\n🛒 <b>Состав:</b>\n"
            )
            
            for item in items:
                item_line = f"• {item['name']} (x{item['quantity']})"
                if item.get('selected_color'):
                    item_line += f", {item['selected_color']}"
                full_msg += f"{item_line}\n"

            return full_msg

            # ПОЛНАЯ ВЕРСИЯ (ДЛЯ ИСТОРИИ И AI)
            details = f"🛍 <b>ЗАКАЗ #{order['id']}</b>\n"
            details += f"📅 Дата создания: {created_at.strftime('%Y-%m-%d %H:%M')}\n"
            if has_backorder:
                details += f"🏁 Доставка: до {est_delivery.strftime('%Y-%m-%d')} <i>(под заказ)</i>\n"
            else:
                details += f"🏁 Доставка: до {est_delivery.strftime('%Y-%m-%d')} <i>(в наличии)</i>\n"
            details += f"🔄 Статус: {status_text}\n"
            details += f"💰 Сумма: {order.get('total', 0):,} сум\n"
            details += f"💳 Оплата: {order.get('payment_method', 'Не указано')}\n"
            
            if order.get('delivery_address'):
                details += f"📍 Адрес: {order['delivery_address']}\n"
            if order.get('customer_name'):
                details += f"👤 Клиент: {order['customer_name']} ({order.get('customer_phone', '')})\n"
            
            details += "\n🛒 <b>СОСТАВ ЗАКАЗА:</b>\n"
            for item in items:
                item_desc = f"- {item['name']} (x{item['quantity']})"
                if item.get('selected_color'):
                    item_desc += f", {item['selected_color']}"
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
                            item_desc += f", {size}"
                
                details += f"{item_desc}\n"
                
            return details
        else:
            cur.close()
            conn.close()
            return None
            
    except Exception as e:
        print(f"❌ Ошибка проверки заказа: {e}")
        return None
def get_pretty_product_info(product_id):
    """
    Формирует красивый HTML-текст о товаре для пользователя.
    Используется ботом для автоматической замены тега [ИНФО:id].
    """
    product = get_product_details(product_id)
    if not product:
        return "<i>Товар не найден.</i>"
    
    # Формируем текст
    price_text = f"{product['price']} сум"
    description = product.get('description')
    if not description or description == 'NULL_DATA':
        description = "<i>Описание этой модели сейчас готовится нашей командой Monvoir.</i>"
    
    res = f"🏷 <b>{product['name']}</b>\n"
    res += f"💰 <b>Цена:</b> {price_text}\n\n"
    res += f"📝 <b>Описание:</b>\n{description}\n\n"
    
    # Формируем матрицу размеров/цветов
    inventory = product.get('inventory', [])
    if inventory:
        res += "📏 <b>Доступные размеры:</b>\n"
        # Группируем по цветам для красоты
        color_groups = {}
        for item in inventory:
            color_raw = item.get('color')
            color = format_colors([color_raw]) if color_raw else "Стандарт"
            if color not in color_groups:
                color_groups[color] = []
            
            size = item.get('attribute1_value') or "Универсальный"
            qty = item.get('quantity', 0)
            if qty > 0:
                color_groups[color].append(f"<code>{size}</code>")
        
        for color, sizes in color_groups.items():
            if sizes:
                res += f"• {color}: {', '.join(sizes)}\n"
            else:
                res += f"• {color}: <i>ожидается поступление</i>\n"
    else:
        res += "📍 <i>Информации о наличии размеров пока нет.</i>"
    
    return res
