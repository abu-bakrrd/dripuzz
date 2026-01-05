from flask import Blueprint, request, jsonify
from backend.database import get_db_connection
import json

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat/messages', methods=['GET'])
def get_messages():
    """Fetch messages for the current user (requires authentication on frontend)"""
    user_id = request.args.get('userId')
    
    if not user_id:
        return jsonify({'error': 'User ID required'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get messages where user is sender or receiver
        cur.execute('''
            SELECT 
                cm.id,
                cm.user_id,
                cm.sender_id,
                cm.content,
                cm.is_read,
                cm.created_at
            FROM chat_messages cm
            WHERE cm.user_id = %s OR cm.sender_id = %s
            ORDER BY cm.created_at ASC
        ''', (user_id, user_id))
        
        messages = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(messages)
    except Exception as e:
        print(f"❌ Error fetching messages: {e}")
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/admin/chat/list', methods=['GET'])
def get_chat_list():
    """Fetch list of users who have chatted, with their last message"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Complex query to get unique users and their last message
        cur.execute('''
            SELECT DISTINCT ON (u.id)
                u.id, 
                u.first_name, 
                u.last_name, 
                u.email,
                u.phone,
                cm.content as last_message,
                cm.created_at as last_message_time,
                (SELECT COUNT(*) FROM chat_messages WHERE user_id = u.id AND sender_id = u.id AND is_read = FALSE) as unread_count
            FROM users u
            JOIN chat_messages cm ON cm.user_id = u.id OR cm.sender_id = u.id
            ORDER BY u.id, cm.created_at DESC
        ''')
        
        chats = cur.fetchall()
        
        # Re-sort by last message time (since DISTINCT ON requires ordering by ID first)
        chats.sort(key=lambda x: x['last_message_time'], reverse=True)
        
        cur.close()
        conn.close()
        
        return jsonify(chats)
    except Exception as e:
        print(f"❌ Error fetching chat list: {e}")
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/admin/chat/<user_id>', methods=['GET'])
def get_admin_user_messages(user_id):
    """Fetch all messages for a specific user (admin view)"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT 
                cm.id,
                cm.user_id,
                cm.sender_id,
                cm.content,
                cm.is_read,
                cm.created_at,
                u.first_name as sender_name
            FROM chat_messages cm
            LEFT JOIN users u ON u.id = cm.sender_id
            WHERE cm.user_id = %s OR cm.sender_id = %s
            ORDER BY cm.created_at ASC
        ''', (user_id, user_id))
        
        messages = cur.fetchall()
        
        # Start looking for user details
        cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
        user_info = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return jsonify({'messages': messages, 'user': user_info})
    except Exception as e:
        print(f"❌ Error fetching user messages: {e}")
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/chat/read', methods=['POST'])
def mark_read():
    """Mark messages as read"""
    data = request.json
    user_id = data.get('userId')
    # If admin is reading, we mark user's messages as read.
    # If user is reading, we mark admin's messages as read.
    # For simplicity, we just mark all unread messages in this conversation as read 
    # where the sender is NOT the current viewer.
    
    sender_id = data.get('senderId') # WHO sent the messages we are reading (the other person)

    if not user_id or not sender_id:
        return jsonify({'error': 'Missing params'}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            UPDATE chat_messages 
            SET is_read = TRUE 
            WHERE (user_id = %s OR sender_id = %s) AND sender_id = %s AND is_read = FALSE
        ''', (user_id, user_id, sender_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
