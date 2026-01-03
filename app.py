import os
import json
from flask import send_from_directory, jsonify, request
from backend import create_app
from backend.database import get_db_connection

app = create_app()

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory(os.path.join(app.static_folder, 'assets'), filename)

@app.route('/sitemap.xml')
def sitemap():
    # Load site URL from config
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, 'config', 'settings.json')
    site_url = "https://monvoir.shop" # Default fallback
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                site_url = config.get('seo', {}).get('siteUrl', site_url)
    except Exception as e:
        print(f"⚠️ Error loading siteUrl for sitemap: {e}")

    # Start XML structure with proper namespace
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    # Add home page
    xml.append('  <url>')
    xml.append(f'    <loc>{site_url}/</loc>')
    xml.append('    <changefreq>daily</changefreq>')
    xml.append('    <priority>1.0</priority>')
    xml.append('  </url>')
    
    # Fetch all products from database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id FROM products')
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        for row in rows:
            product_url = f"{site_url}/product/{row['id']}"
            xml.append('  <url>')
            xml.append(f'    <loc>{product_url}</loc>')
            xml.append('    <changefreq>weekly</changefreq>')
            xml.append('    <priority>0.8</priority>')
            xml.append('  </url>')
    except Exception as e:
        print(f"⚠️ Error fetching products for sitemap: {e}")
        
    xml.append('</urlset>')
    
    return "\n".join(xml), 200, {'Content-Type': 'application/xml'}

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path.startswith('api/'):
        return jsonify({'error': 'Not found'}), 404
    
    # Simple SEO stub for now, keeping it robust
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
