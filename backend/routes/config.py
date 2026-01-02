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
