"""
Скрипт для добавления тестовых товаров в базу данных
Используется для локального тестирования AI бота
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """Подключение к базе данных"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        if 'neon.tech' in database_url or 'amazonaws.com' in database_url:
            if 'sslmode=' not in database_url:
                database_url = database_url + ('&' if '?' in database_url else '?') + 'sslmode=require'
        return psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        return psycopg2.connect(
            host=os.getenv('PGHOST', 'localhost'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('PGUSER', 'postgres'),
            password=os.getenv('PGPASSWORD', ''),
            database=os.getenv('PGDATABASE', 'shop_db'),
            cursor_factory=RealDictCursor
        )


def create_test_category():
    """Создать тестовую категорию"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Проверяем, есть ли уже категория
    cur.execute("SELECT id FROM categories WHERE name = 'Одежда' LIMIT 1")
    category = cur.fetchone()
    
    if category:
        category_id = category['id']
        print(f"✅ Категория 'Одежда' уже существует (ID: {category_id})")
    else:
        cur.execute("""
            INSERT INTO categories (name, icon, sort_order)
            VALUES ('Одежда', '👕', 1)
            RETURNING id
        """)
        category_id = cur.fetchone()['id']
        conn.commit()
        print(f"✅ Создана категория 'Одежда' (ID: {category_id})")
    
    cur.close()
    conn.close()
    return category_id


def add_test_products(category_id):
    """Добавить тестовые товары"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Тестовые товары
    test_products = [
        {
            'name': 'Футболка Nike Pro',
            'description': 'Спортивная футболка из дышащей ткани',
            'price': 150000,
            'images': ['https://via.placeholder.com/400x400?text=Nike+Pro'],
            'category_id': category_id,
            'colors': ['#000000', '#FFFFFF', '#0000FF'],  # черный, белый, синий
            'attributes': [
                {'name': 'Размер', 'values': ['S', 'M', 'L', 'XL']}
            ]
        },
        {
            'name': 'Кроссовки Adidas Ultraboost',
            'description': 'Беговые кроссовки с технологией Boost',
            'price': 450000,
            'images': ['https://via.placeholder.com/400x400?text=Adidas+Ultraboost'],
            'category_id': category_id,
            'colors': ['#FFFFFF', '#000000'],  # белый, черный
            'attributes': [
                {'name': 'Размер', 'values': ['40', '41', '42', '43', '44']}
            ]
        },
        {
            'name': 'Джинсы Levi\'s 501',
            'description': 'Классические прямые джинсы',
            'price': 350000,
            'images': ['https://via.placeholder.com/400x400?text=Levis+501'],
            'category_id': category_id,
            'colors': ['#0000FF', '#000000'],  # синий, черный
            'attributes': [
                {'name': 'Размер', 'values': ['30', '32', '34', '36']}
            ]
        },
        {
            'name': 'Куртка The North Face',
            'description': 'Зимняя куртка с утеплителем',
            'price': 850000,
            'images': ['https://via.placeholder.com/400x400?text=North+Face'],
            'category_id': category_id,
            'colors': ['#000000', '#FF0000', '#008000'],  # черный, красный, зеленый
            'attributes': [
                {'name': 'Размер', 'values': ['S', 'M', 'L', 'XL', 'XXL']}
            ]
        }
    ]
    
    product_ids = []
    
    for product_data in test_products:
        # Проверяем, есть ли уже такой товар
        cur.execute("SELECT id FROM products WHERE name = %s LIMIT 1", (product_data['name'],))
        existing = cur.fetchone()
        
        if existing:
            print(f"⏭️  Товар '{product_data['name']}' уже существует, пропускаем")
            product_ids.append(existing['id'])
            continue
        
        # Добавляем товар
        cur.execute("""
            INSERT INTO products (name, description, price, images, category_id, colors, attributes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            product_data['name'],
            product_data['description'],
            product_data['price'],
            product_data['images'],
            product_data['category_id'],
            product_data['colors'],
            json.dumps(product_data['attributes'])
        ))
        
        product_id = cur.fetchone()['id']
        product_ids.append(product_id)
        print(f"✅ Добавлен товар: {product_data['name']} (ID: {product_id})")
    
    conn.commit()
    cur.close()
    conn.close()
    
    return product_ids


def add_test_inventory(product_ids):
    """Добавить тестовые данные о наличии"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Примеры наличия для первого товара (Футболка Nike Pro)
    if len(product_ids) > 0:
        inventory_data = [
            (product_ids[0], '#000000', 'S', None, 5),  # черный S - 5 шт
            (product_ids[0], '#000000', 'M', None, 3),  # черный M - 3 шт
            (product_ids[0], '#FFFFFF', 'L', None, 2),  # белый L - 2 шт
            (product_ids[0], '#0000FF', 'M', None, 4),  # синий M - 4 шт
        ]
        
        for data in inventory_data:
            # Проверяем, есть ли уже такая запись
            cur.execute("""
                SELECT id FROM product_inventory 
                WHERE product_id = %s AND color = %s AND attribute1_value = %s
                LIMIT 1
            """, (data[0], data[1], data[2]))
            
            if cur.fetchone():
                continue
            
            cur.execute("""
                INSERT INTO product_inventory 
                (product_id, color, attribute1_value, attribute2_value, quantity)
                VALUES (%s, %s, %s, %s, %s)
            """, data)
        
        print(f"✅ Добавлены данные о наличии для футболки")
    
    # Для кроссовок
    if len(product_ids) > 1:
        inventory_data = [
            (product_ids[1], '#FFFFFF', '41', None, 3),  # белый 41 - 3 шт
            (product_ids[1], '#FFFFFF', '42', None, 5),  # белый 42 - 5 шт
            (product_ids[1], '#000000', '43', None, 2),  # черный 43 - 2 шт
        ]
        
        for data in inventory_data:
            cur.execute("""
                SELECT id FROM product_inventory 
                WHERE product_id = %s AND color = %s AND attribute1_value = %s
                LIMIT 1
            """, (data[0], data[1], data[2]))
            
            if cur.fetchone():
                continue
            
            cur.execute("""
                INSERT INTO product_inventory 
                (product_id, color, attribute1_value, attribute2_value, quantity)
                VALUES (%s, %s, %s, %s, %s)
            """, data)
        
        print(f"✅ Добавлены данные о наличии для кроссовок")
    
    conn.commit()
    cur.close()
    conn.close()


def main():
    """Главная функция"""
    print("🔧 Создание тестовых данных для AI бота...")
    print()
    
    try:
        # Создаем категорию
        category_id = create_test_category()
        
        # Добавляем товары
        product_ids = add_test_products(category_id)
        
        # Добавляем данные о наличии
        add_test_inventory(product_ids)
        
        print()
        print("✅ Тестовые данные успешно добавлены!")
        print()
        print("📊 Добавлено:")
        print(f"   - 1 категория")
        print(f"   - {len(product_ids)} товаров")
        print(f"   - Данные о наличии")
        print()
        print("🤖 Теперь можете запустить AI бота и протестировать!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()
