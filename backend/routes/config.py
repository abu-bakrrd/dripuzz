import json
from flask import Blueprint, jsonify, current_app
from backend.database import get_platform_setting
import os

config_bp = Blueprint('config', __name__)

@config_bp.route('/config', methods=['GET'])
def get_config():
    # Robust path resolution for settings.json
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    config_path = os.path.join(project_root, 'config', 'settings.json')
    
    try:
        if not os.path.exists(config_path):
            print(f"⚠️ settings.json not found at: {config_path}")
            raise FileNotFoundError(f"settings.json not found at: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error loading settings.json: {e}")
        # Fallback to empty dict or basic structure
        config = {
            "shopName": "MiniOrder",
            "currency": {"symbol": "UZS", "code": "UZS", "position": "after"}
        }

    # Overwrite from database if settings exist
    telegram_bot_url = get_platform_setting('telegram_bot_url')
    if telegram_bot_url:
        config['telegramBotUrl'] = telegram_bot_url

    # Yandex Maps from database
    try:
        from backend.database import get_yandex_maps_config
        yandex_cfg = get_yandex_maps_config()
        if yandex_cfg.get('api_key'):
            config['yandexMaps'] = {
                'apiKey': yandex_cfg['api_key'],
                'defaultCenter': [float(yandex_cfg['default_lat']), float(yandex_cfg['default_lng'])],
                'defaultZoom': yandex_cfg['default_zoom']
            }
    except Exception as e:
        print(f"❌ Error fetching Yandex Maps config: {e}")

    # Payment settings from database
    try:
        from backend.database import get_payment_config
        for p in ['click', 'payme', 'uzum', 'card_transfer']:
            p_cfg = get_payment_config(p)
            if p_cfg.get('enabled') is not None:
                if 'payment' not in config: config['payment'] = {}
                config['payment'][p] = p_cfg
    except Exception as e:
        print(f"❌ Error fetching payment config: {e}")

    # Fetch categories from database
    try:
        from backend.database import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, name, icon FROM categories ORDER BY sort_order, name')
        db_categories = cur.fetchall()
        cur.close()
        conn.close()
        
        if db_categories:
            config['categories'] = db_categories
    except Exception as e:
        print(f"❌ Error fetching categories for config: {e}")

    return jsonify(config)
