from flask import Blueprint, request, jsonify, session, Response
from werkzeug.security import generate_password_hash, check_password_hash
import json
import io
import csv
import requests
from datetime import datetime

from ..database import (
    get_db_connection, get_platform_setting, set_platform_setting,
    get_cloudinary_config, get_telegram_config, get_smtp_config, get_payment_config, get_yandex_maps_config
)
from ..utils.auth import require_admin, require_superadmin, admin_required_response, superadmin_required_response
from ..services.cloud_service import upload_image_to_cloud, test_cloud_connection
from ..services.email_service import send_email

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user or not user.get('password_hash') or not check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.get('is_admin'):
        return jsonify({'error': 'Access denied. Admin privileges required.'}), 403
    
    session.permanent = True
    session['user_id'] = user['id']
    
    return jsonify({
        'user': {'id': user['id'], 'email': user['email'], 'first_name': user.get('first_name'), 'is_admin': True},
        'message': 'Admin login successful'
    })

@admin_bp.route('/setup', methods=['POST'])
def admin_setup():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = TRUE')
    if cur.fetchone()['count'] > 0:
        cur.close()
        conn.close()
        return jsonify({'error': 'Admin already exists'}), 403
    
    cur.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cur.fetchone()
    if not user or not check_password_hash(user['password_hash'], password):
        cur.close()
        conn.close()
        return jsonify({'error': 'Invalid credentials or user not registered'}), 401
    
    cur.execute('UPDATE users SET is_admin = TRUE, is_superadmin = TRUE WHERE id = %s RETURNING *', (user['id'],))
    updated_user = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    session.permanent = True
    session['user_id'] = updated_user['id']
    return jsonify({'user': updated_user, 'message': 'Admin setup successful'})

@admin_bp.route('/check-setup', methods=['GET'])
def admin_check_setup():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as count FROM users WHERE is_admin = TRUE')
    admin_count = cur.fetchone()['count']
    cur.close()
    conn.close()
    return jsonify({'needs_setup': admin_count == 0})

@admin_bp.route('/me', methods=['GET'])
def admin_me():
    admin_id = require_admin()
    if not admin_id: return jsonify({'error': 'Not authorized'}), 401
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, email, first_name, last_name, is_admin, is_superadmin FROM users WHERE id = %s', (admin_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return jsonify({'user': user})

# Admin Management
@admin_bp.route('/admins', methods=['GET'])
def get_all_admins():
    if not require_superadmin(): return superadmin_required_response()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, email, first_name, last_name, phone, is_admin, is_superadmin, created_at FROM users WHERE is_admin = TRUE ORDER BY is_superadmin DESC, created_at ASC')
    admins = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(admins)

# Orders, Products, Categories, Inventory etc.
@admin_bp.route('/orders', methods=['GET'])
def admin_get_orders():
    if not require_admin(): return admin_required_response()
    status = request.args.get('status')
    conn = get_db_connection()
    cur = conn.cursor()
    query = 'SELECT o.*, u.email as user_email, u.first_name, u.last_name FROM orders o LEFT JOIN users u ON o.user_id = u.id'
    params = []
    if status:
        query += ' WHERE o.status = %s'
        params.append(status)
    query += ' ORDER BY o.created_at DESC LIMIT 50'
    cur.execute(query, params)
    orders = cur.fetchall()
    for order in orders:
        cur.execute('SELECT oi.*, p.images FROM order_items oi LEFT JOIN products p ON oi.product_id = p.id WHERE oi.order_id = %s', (order['id'],))
        order['items'] = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(orders)

@admin_bp.route('/products', methods=['GET'])
def admin_get_products():
    if not require_admin(): return admin_required_response()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM products ORDER BY name')
    products = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(products)

@admin_bp.route('/inventory', methods=['GET'])
def admin_get_inventory():
    if not require_admin(): return admin_required_response()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT i.*, p.name as product_name FROM product_inventory i JOIN products p ON i.product_id = p.id ORDER BY p.name')
    inventory = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(inventory)

# Settings
@admin_bp.route('/settings/cloudinary', methods=['GET', 'PUT'])
def admin_cloudinary_settings():
    if not require_admin(): return admin_required_response()
    if request.method == 'GET':
        config = get_cloudinary_config()
        return jsonify({'cloud_name': config['cloud_name'], 'api_key': config['api_key'], 'has_api_secret': bool(config['api_secret'])})
    
    data = request.json
    set_platform_setting('cloudinary_cloud_name', data.get('cloud_name'), False)
    set_platform_setting('cloudinary_api_key', data.get('api_key'), False)
    if data.get('api_secret'):
        set_platform_setting('cloudinary_api_secret', data.get('api_secret'), True)
    return jsonify({'message': 'Settings saved'})

# Stats
@admin_bp.route('/statistics', methods=['GET'])
def admin_get_statistics():
    if not require_admin(): return admin_required_response()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM users'); u_count = cur.fetchone()['count']
    cur.execute('SELECT COUNT(*) FROM orders'); o_count = cur.fetchone()['count']
    cur.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE status != 'cancelled'"); rev = cur.fetchone()['sum']
    cur.close(); conn.close()
    return jsonify({'total_users': u_count, 'total_orders': o_count, 'total_revenue': rev})

@admin_bp.route('/settings/cloudinary/test', methods=['POST'])
def admin_test_cloudinary():
    if not require_admin(): return admin_required_response()
    ok, res = test_cloud_connection()
    return jsonify({'success': ok, 'message': 'Cloudinary connected' if ok else res})

@admin_bp.route('/settings/telegram/test', methods=['POST'])
def admin_test_telegram():
    if not require_admin(): return admin_required_response()
    from ..services.tg_service import send_telegram_notification
    # Generic test message
    cfg = get_telegram_config()
    if not cfg['bot_token'] or not cfg['admin_chat_id']:
        return jsonify({'success': False, 'error': 'Telegram not configured'})
    
    url = f"https://api.telegram.org/bot{cfg['bot_token']}/sendMessage"
    payload = {'chat_id': cfg['admin_chat_id'], 'text': '✅ Test message from Admin Panel'}
    resp = requests.post(url, json=payload, timeout=10)
    return jsonify({'success': resp.status_code == 200, 'error': resp.text if resp.status_code != 200 else None})

@admin_bp.route('/settings/smtp', methods=['GET', 'PUT'])
def admin_smtp_settings():
    if not require_admin(): return admin_required_response()
    if request.method == 'GET':
        cfg = get_smtp_config()
        return jsonify({'host': cfg['host'], 'port': cfg['port'], 'user': cfg['user'], 'has_password': bool(cfg['password']), 'from_email': cfg['from_email'], 'from_name': cfg['from_name'], 'use_tls': cfg['use_tls']})
    data = request.json
    for k, v in data.items():
        if k == 'password' and v: set_platform_setting('smtp_password', v, True)
        elif k != 'password': set_platform_setting(f'smtp_{k}', str(v), False)
    return jsonify({'message': 'Saved'})

@admin_bp.route('/settings/payments', methods=['GET'])
def admin_get_payment_settings():
    if not require_admin(): return admin_required_response()
    return jsonify({
        'click': get_payment_config('click'),
        'payme': get_payment_config('payme'),
        'uzum': get_payment_config('uzum'),
        'card_transfer': get_payment_config('card_transfer')
    })

@admin_bp.route('/inventory/export', methods=['GET'])
def admin_export_inventory():
    if not require_admin(): return admin_required_response()
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute('SELECT i.*, p.name FROM product_inventory i JOIN products p ON i.product_id = p.id')
    items = cur.fetchall(); cur.close(); conn.close()
    
    si = io.StringIO()
    cw = csv.DictWriter(si, fieldnames=['id', 'product_id', 'name', 'color', 'attribute1_value', 'attribute2_value', 'quantity', 'backorder_lead_time_days', 'created_at', 'updated_at'])
    cw.writeheader()
    cw.writerows(items)
    return Response(si.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=inventory.csv'})

# Categories Management
@admin_bp.route('/categories', methods=['GET'])
def admin_get_categories():
    if not require_admin(): return admin_required_response()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM categories ORDER BY sort_order ASC, name ASC')
    categories = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(categories)

@admin_bp.route('/categories', methods=['POST'])
def admin_create_category():
    if not require_admin(): return admin_required_response()
    data = request.json
    name = data.get('name')
    icon = data.get('icon')
    sort_order = data.get('sort_order', 0)
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
        
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO categories (name, icon, sort_order) VALUES (%s, %s, %s) RETURNING id',
        (name, icon, sort_order)
    )
    new_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'id': new_id, 'message': 'Category created'})

@admin_bp.route('/categories/<category_id>', methods=['PUT'])
def admin_update_category(category_id):
    if not require_admin(): return admin_required_response()
    data = request.json
    name = data.get('name')
    icon = data.get('icon')
    sort_order = data.get('sort_order', 0)
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        'UPDATE categories SET name = %s, icon = %s, sort_order = %s WHERE id = %s',
        (name, icon, sort_order, category_id)
    )
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Category updated'})

@admin_bp.route('/categories/<category_id>', methods=['DELETE'])
def admin_delete_category(category_id):
    if not require_admin(): return admin_required_response()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM categories WHERE id = %s', (category_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Category deleted'})
