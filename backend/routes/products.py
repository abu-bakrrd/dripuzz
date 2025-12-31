from flask import Blueprint, request, jsonify
from ..database import get_db_connection

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_products():
    try:
        category = request.args.get('category')
        conn = get_db_connection()
        cur = conn.cursor()
        if category:
            cur.execute('SELECT * FROM products WHERE category_id = %s', (category,))
        else:
            cur.execute('SELECT * FROM products')
        products = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(products)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        product = cur.fetchone()
        if not product:
            cur.close()
            conn.close()
            return jsonify({'error': 'Product not found'}), 404
        
        cur.execute('SELECT color, attribute1_value, attribute2_value, quantity, backorder_lead_time_days FROM product_inventory WHERE product_id = %s', (product_id,))
        inventory = cur.fetchall()
        cur.close()
        conn.close()
        
        product_data = dict(product)
        product_data['inventory'] = inventory
        return jsonify(product_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/products/check', methods=['POST'])
def check_products_exist():
    try:
        data = request.json
        product_ids = data.get('product_ids', [])
        if not product_ids:
            return jsonify({'existing': [], 'missing': []})
        
        conn = get_db_connection()
        cur = conn.cursor()
        placeholders = ','.join(['%s'] * len(product_ids))
        cur.execute(f'SELECT id FROM products WHERE id IN ({placeholders})', tuple(product_ids))
        existing_ids = [p['id'] for p in cur.fetchall()]
        missing_ids = [pid for pid in product_ids if pid not in existing_ids]
        cur.close()
        conn.close()
        return jsonify({'existing': existing_ids, 'missing': missing_ids})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM categories ORDER BY sort_order, name')
        categories = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
