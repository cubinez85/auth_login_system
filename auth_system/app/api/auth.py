from flask import Blueprint, request, jsonify, g, current_app
from app import db, limiter
from app.models.user import User
from app.models.token import TokenBlacklist
from app.utils.jwt_helper import (
    generate_tokens, 
    verify_refresh_token, 
    decode_token, 
    blacklist_token,
    get_token_expires
)
from datetime import datetime
import re
import jwt

# ВАЖНО: url_prefix задаётся ЗДЕСЬ, а не при регистрации в __init__.py
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# --- Валидаторы ---

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter'
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one number'
    return True, 'Password is valid'

def get_current_user():
    """Получает пользователя из JWT токена в заголовке Authorization"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    
    if 'error' in payload or 'user_id' not in payload:
        return None
    
    user = User.query.filter_by(id=payload['user_id'], is_active=True).first()
    return user

# --- Эндпоинты ---

@auth_bp.route('/register/', methods=['POST'])
@limiter.limit("5/hour")
def register():
    data = request.get_json()
    
    required_fields = ['email', 'password', 'confirm_password', 'last_name', 'first_name']
    for field in required_fields:
        if not data or field not in data:
            return jsonify({'message': f'Missing field: {field}'}), 400

    if not validate_email(data['email']):
        return jsonify({'message': 'Invalid email format'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 409

    valid, message = validate_password(data['password'])
    if not valid:
        return jsonify({'message': message}), 400

    if data['password'] != data['confirm_password']:
        return jsonify({'message': 'Passwords do not match'}), 400

    user = User(
        email=data['email'],
        last_name=data['last_name'],
        first_name=data['first_name'],
        middle_name=data.get('middle_name', '')
    )
    user.password = data['password']

    try:
        db.session.add(user)
        db.session.commit()
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name()
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Registration failed: {str(e)}'}), 500

@auth_bp.route('/login/', methods=['POST'])
@limiter.limit("10/minute")
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Email and password required'}), 400

    user = User.query.filter_by(email=data['email'], is_active=True).first()

    if not user or not user.verify_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    tokens = generate_tokens(user.id)

    return jsonify({
        'message': 'Login successful',
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token'],
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.get_full_name()
        }
    }), 200

@auth_bp.route('/refresh/', methods=['POST'])
@limiter.limit("5/minute")
def refresh():
    data = request.get_json()
    
    if not data or not data.get('refresh_token'):
        return jsonify({'message': 'Refresh token required'}), 400

    user_id = verify_refresh_token(data['refresh_token'])
    if not user_id:
        return jsonify({'message': 'Invalid refresh token'}), 401

    user = User.query.get(user_id)
    if not user or not user.is_active:
        return jsonify({'message': 'User not found or inactive'}), 401

    tokens = generate_tokens(user.id)
    return jsonify({
        'access_token': tokens['access_token'],
        'refresh_token': tokens['refresh_token']
    }), 200

@auth_bp.route('/logout/', methods=['POST'])
@limiter.limit("30/minute")
def logout():
    """Инвалидация токена через blacklist"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Authorization header required'}), 400

    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    
    # Если токен уже истек — всё равно считаем logout успешным
    if 'error' in payload and payload['error'] != 'Signature expired':
        return jsonify({'message': payload['error']}), 400

    expires_at = get_token_expires(token)
    if blacklist_token(token, expires_at):
        return jsonify({'message': 'Successfully logged out'}), 200
    else:
        return jsonify({'message': 'Logout failed'}), 500

@auth_bp.route('/profile/', methods=['PUT'])
@limiter.limit("10/minute")
def update_profile():
    """Обновление профиля: имя, фамилия, отчество"""
    user = get_current_user()
    if not user:
        return jsonify({'message': 'Unauthorized or invalid token'}), 401

    data = request.get_json()
    
    # ✅ ИСПРАВЛЕНО: добавлено 'in data:'
    if 'last_name' in data:
        user.last_name = data['last_name']
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'middle_name' in data:
        user.middle_name = data['middle_name']

    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.get_full_name()
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Update failed: {str(e)}'}), 500

@auth_bp.route('/profile/', methods=['DELETE'])
@limiter.limit("5/minute")
def delete_profile():
    """Мягкое удаление аккаунта + инвалидация токенов"""
    user = get_current_user()
    if not user:
        return jsonify({'message': 'Unauthorized'}), 401

    # Мягкое удаление
    user.soft_delete()
    
    # Инвалидация текущего токена
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(" ")[1]
        expires_at = get_token_expires(token)
        blacklist_token(token, expires_at)

    try:
        db.session.commit()
        return jsonify({'message': 'Account deactivated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Deletion failed: {str(e)}'}), 500
