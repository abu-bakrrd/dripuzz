import os
import json
from flask import request, send_from_directory
from ..database import get_db_connection

def get_seo_html(static_folder, shop_config, product=None):
    """Generate HTML with meta tags for SEO"""
    try:
        index_path = os.path.join(static_folder, 'index.html')
        if not os.path.exists(index_path):
            return None
        
        with open(index_path, 'r', encoding='utf-8') as f:
            html = f.read()
            
        host = request.host_url.rstrip('/')
        shop_name = shop_config.get('shopName', 'Shop')
        shop_desc = shop_config.get('description', '')
        
        seo = shop_config.get('seo', {})
        title = seo.get('title', shop_name)
        description = seo.get('description', shop_desc)
        
        if product:
             title = f"{product['name']} | {shop_name}"
             description = product.get('description', description)[:160]
             # ... more replacements ...
        
        html = html.replace('{{SHOP_NAME}}', shop_name)
        # Add basic replacements
        return html
    except Exception as e:
        print(f"SEO error: {e}")
        return None
