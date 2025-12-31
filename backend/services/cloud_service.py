import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask import jsonify, request
from ..database import get_cloudinary_config

def upload_image_to_cloud(file, folder='telegram_shop_products'):
    """Upload image to Cloudinary"""
    try:
        config = get_cloudinary_config()
        if not all([config['cloud_name'], config['api_key'], config['api_secret']]):
            return None, "Cloudinary is not configured"
        
        cloudinary.config(
            cloud_name=config['cloud_name'],
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type='image'
        )
        return result, None
    except Exception as e:
        return None, str(e)

def test_cloud_connection():
    """Test Cloudinary connection"""
    try:
        config = get_cloudinary_config()
        if not all([config['cloud_name'], config['api_key'], config['api_secret']]):
            return False, "Missing credentials"
        
        cloudinary.config(
            cloud_name=config['cloud_name'],
            api_key=config['api_key'],
            api_secret=config['api_secret']
        )
        
        result = cloudinary.api.usage()
        return True, result
    except Exception as e:
        return False, str(e)
