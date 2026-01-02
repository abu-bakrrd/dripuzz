from flask import Blueprint, request, jsonify
from ..services.cloud_service import upload_image_to_cloud
from ..utils.auth import require_admin, admin_required_response

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload', methods=['POST'])
def upload_file():
    if not require_admin(): return admin_required_response()
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    try:
        # Read file content
        file_content = file.read()
        
        # Upload using the service
        url = upload_image_to_cloud(file_content)
        
        if not url:
            return jsonify({'error': 'Failed to upload image'}), 500
            
        return jsonify({'secure_url': url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
