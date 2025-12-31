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
    # Basic sitemap logic
    return "<?xml version='1.0' encoding='UTF-8'?><urlset></urlset>", 200, {'Content-Type': 'application/xml'}

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
