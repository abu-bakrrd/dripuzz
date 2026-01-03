import json
from flask import Blueprint, jsonify, current_app
from backend.database import get_platform_setting
import os

config_bp = Blueprint('config', __name__)

@config_bp.route('/config', methods=['GET'])
def get_config():
    # Base path for config/settings.json
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'settings.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error reading settings.json: {e}")
        # Fallback to empty dict or basic structure
        config = {
            "shopName": "MiniOrder",
            "currency": {"symbol": "UZS", "code": "UZS", "position": "after"}
        }

    # Overwrite from database if settings exist
    telegram_bot_url = get_platform_setting('telegram_bot_url')
    if telegram_bot_url:
        config['telegramBotUrl'] = telegram_bot_url

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

    # Ensure status translations from DB are used if available (optional)
    # For now, we trust settings.json as the single source for UI/Texts
    
    return jsonify(config)
