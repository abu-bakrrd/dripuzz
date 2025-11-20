import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json


def get_db_connection():
    """Creates database connection"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        if 'sslmode=' not in database_url:
            database_url = database_url + ('&' if '?' in database_url else '?') + 'sslmode=require'
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
    else:
        conn = psycopg2.connect(
            host=os.getenv('PGHOST'),
            port=os.getenv('PGPORT', '5432'),
            user=os.getenv('PGUSER'),
            password=os.getenv('PGPASSWORD'),
            database=os.getenv('PGDATABASE'),
            sslmode='require',
            cursor_factory=RealDictCursor
        )
    return conn


def get_config():
    """
    Loads shop configuration from config/settings.json
    
    Returns:
        dict: Configuration dictionary or None if error
    """
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'settings.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def get_categories_from_config():
    """
    Gets categories from settingsbot.json file
    
    Returns:
        list: Array of category dictionaries or empty array if error
    """
    try:
        with open('settingsbot.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('categories', [])
    except FileNotFoundError:
        print("⚠️ Файл settingsbot.json не найден.")
        return []
    except Exception as e:
        print(f"❌ Ошибка загрузки категорий: {e}")
        return []


def add_product(name, description, price, images, category_id=None, colors=None, attributes=None):
    """
    Adds new product to database
    
    Parameters:
        name (str): Product name
        description (str): Product description
        price (int): Product price in cents
        images (list): Array of image URLs
        category_id (str, optional): Category ID (must match category ID from config)
        colors (list, optional): Array of HEX color codes (e.g., ["#FF0000", "#00FF00"])
        attributes (list, optional): Array of attribute dicts (e.g., [{"name": "Size", "values": ["S", "M", "L"]}])
    
    Returns:
        dict: Dictionary with created product data or None if error
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO products (name, description, price, images, category_id, colors, attributes) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *',
            (name, description, price, images, category_id, colors, json.dumps(attributes) if attributes else None)
        )
        product = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return product
    except Exception as e:
        print(f"Error adding product: {e}")
        return None


def delete_product(product_id):
    """
    Deletes product from database
    
    Parameters:
        product_id (str): Product ID to delete
    
    Returns:
        bool: True if product deleted, False if error
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM products WHERE id = %s', (product_id,))
        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        return deleted_count > 0
    except Exception as e:
        print(f"Error deleting product: {e}")
        return False


def get_all_products(category_id=None):
    """
    Gets all products from database (with optional category filter)
    
    Parameters:
        category_id (str, optional): Category ID for filtering
    
    Returns:
        list: Array of product dictionaries or empty array if error
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if category_id:
            cur.execute('SELECT * FROM products WHERE category_id = %s', (category_id,))
        else:
            cur.execute('SELECT * FROM products')
        
        products = cur.fetchall()
        cur.close()
        conn.close()
        return products
    except Exception as e:
        print(f"Error getting products: {e}")
        return []


def get_product_by_id(product_id):
    """
    Gets product by ID
    
    Parameters:
        product_id (str): Product ID
    
    Returns:
        dict: Dictionary with product data or None if not found
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        product = cur.fetchone()
        cur.close()
        conn.close()
        return product
    except Exception as e:
        print(f"Error getting product: {e}")
        return None


def find_products_by_name(name):
    """
    Searches products by name (partial match)
    
    Parameters:
        name (str): Product name or part of name
    
    Returns:
        list: Array of product dictionaries or empty array
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM products WHERE name ILIKE %s', (f'%{name}%',))
        products = cur.fetchall()
        cur.close()
        conn.close()
        return products
    except Exception as e:
        print(f"Error searching products: {e}")
        return []


def update_product(product_id, name=None, description=None, price=None, images=None, category_id=None, colors=None, attributes=None):
    """
    Updates product in database
    
    Parameters:
        product_id (str): Product ID to update
        name (str, optional): New product name
        description (str, optional): New description
        price (int, optional): New price in cents
        images (list, optional): New array of image URLs
        category_id (str, optional): New category ID
        colors (list, optional): New array of HEX color codes
        attributes (list, optional): New array of attribute dicts
    
    Returns:
        dict: Updated product data or None if error
    """
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Build update query dynamically
        updates = []
        values = []
        
        if name is not None:
            updates.append("name = %s")
            values.append(name)
        if description is not None:
            updates.append("description = %s")
            values.append(description)
        if price is not None:
            updates.append("price = %s")
            values.append(price)
        if images is not None:
            updates.append("images = %s")
            values.append(images)
        if category_id is not None:
            updates.append("category_id = %s")
            values.append(category_id)
        if colors is not None:
            updates.append("colors = %s")
            values.append(colors)
        if attributes is not None:
            updates.append("attributes = %s")
            values.append(json.dumps(attributes) if attributes else None)
        
        if not updates:
            return None
        
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s RETURNING *"
        
        cur.execute(query, values)
        product = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return product
    except Exception as e:
        print(f"Error updating product: {e}")
        return None


# Example usage
if __name__ == "__main__":
    print("=== Database Operations Example ===\n")
    
    # 1. Get all categories from config
    print("1. All categories (from config):")
    categories = get_categories_from_config()
    for cat in categories:
        print(f"   ID: {cat['id']}, Name: {cat['name']}, Icon: {cat['icon']}")
    print()
    
    # 2. Get all products
    print("2. All products:")
    products = get_all_products()
    for prod in products[:3]:  # Show first 3
        print(f"   ID: {prod['id']}, Name: {prod['name']}, Price: {prod['price']}")
    print(f"   ... total {len(products)} products\n")
    
    # 3. Search products by name
    print("3. Search products with 'Product' in name:")
    found = find_products_by_name("Product")
    for prod in found[:3]:  # Show first 3
        print(f"   ID: {prod['id']}, Name: {prod['name']}")
    print()
    
    # 4. Add new product (example - uncomment to test)
    # print("4. Adding new product:")
    # if categories:
    #     new_product = add_product(
    #         name="New Product Example",
    #         description="Example product description",
    #         price=19999,
    #         images=["https://example.com/image1.jpg"],
    #         category_id=categories[0]['id']
    #     )
    #     if new_product:
    #         print(f"   ✓ Product added: {new_product['name']} (ID: {new_product['id']})\n")
    #         
    #         # 5. Update product
    #         print("5. Updating product:")
    #         updated = update_product(
    #             new_product['id'],
    #             price=24999,
    #             description="Updated description"
    #         )
    #         if updated:
    #             print(f"   ✓ Product updated: new price = {updated['price']}\n")
    #         
    #         # 6. Delete product
    #         print("6. Deleting product:")
    #         if delete_product(new_product['id']):
    #             print(f"   ✓ Product deleted (ID: {new_product['id']})")
