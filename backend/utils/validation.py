import re

def validate_email(email):
    """Validate email format"""
    if not email:
        return False, "Email обязателен"
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Неверный формат email"
    
    return True, None

def validate_phone(phone):
    """Validate phone format - accepts various formats"""
    if not phone:
        return True, None  # Phone is optional
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Check if it's a valid phone number (7-15 digits, optionally starting with +)
    if cleaned.startswith('+'):
        digits = cleaned[1:]
    else:
        digits = cleaned
    
    if len(digits) < 7 or len(digits) > 15:
        return False, "Телефон должен содержать от 7 до 15 цифр"
    
    if not digits.isdigit():
        return False, "Телефон должен содержать только цифры"
    
    return True, None
