from flask import Blueprint, jsonify
import os

config_bp = Blueprint('config', __name__)

@config_bp.route('/config', methods=['GET'])
def get_config():
    return jsonify({
        'siteName': os.getenv('SITE_NAME', 'MiniOrder'),
        'currency': 'UZS',
        'orderStatuses': {
            'new': 'Новый',
            'confirmed': 'Подтверждён',
            'pending': 'В ожидании',
            'reviewing': 'Рассматривается',
            'awaiting_payment': 'Ожидает оплаты',
            'paid': 'Оплачен',
            'processing': 'Собирается',
            'shipped': 'В пути',
            'delivered': 'Доставлен',
            'cancelled': 'Отменён'
        },
        'paymentMethods': {
            'click': 'Click',
            'payme': 'Payme',
            'uzum': 'Uzum Bank',
            'card_transfer': 'Перевод на карту'
        }
    })

@config_bp.route('/config/version', methods=['GET'])
def get_config_version():
    from ..database import get_db_connection
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Get the latest update timestamp from all relevant tables
        cur.execute('''
            SELECT CAST(EXTRACT(EPOCH FROM GREATEST(
                COALESCE((SELECT MAX(updated_at) FROM products), '1970-01-01'::timestamp),
                COALESCE((SELECT MAX(updated_at) FROM categories), '1970-01-01'::timestamp),
                COALESCE((SELECT MAX(updated_at) FROM platform_settings), '1970-01-01'::timestamp),
                COALESCE((SELECT MAX(updated_at) FROM product_inventory), '1970-01-01'::timestamp)
            )) AS BIGINT) as version
        ''')
        result = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({'version': result['version'] if result and result['version'] else 0})
    except Exception:
        return jsonify({'version': 0})
