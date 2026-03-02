from flask import Blueprint, jsonify, request, g
from app import db
from app.decorators.permission import admin_required, token_required
from app.models.user import User
from app.models.permission import Role, Permission, Resource, Action, UserRole, UserPermission
import logging

logger = logging.getLogger(__name__)
admin_api_bp = Blueprint('admin_api', __name__)

@admin_api_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        return jsonify({
            'users': [{
                'id': u.id,
                'email': u.email,
                'full_name': u.get_full_name(),
                'is_active': u.is_active,
                'is_superuser': u.is_superuser,
                'created_at': u.created_at.isoformat() if u.created_at else None
            } for u in users]
        }), 200
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@admin_api_bp.route('/users/<int:user_id>/roles', methods=['GET'])
@token_required
@admin_required
def get_user_roles(user_id):
    """Get roles for a specific user"""
    try:
        user = User.query.get_or_404(user_id)
        user_roles = UserRole.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'user_id': user_id,
            'user_email': user.email,
            'roles': [{
                'id': ur.role.id,
                'name': ur.role.name,
                'description': ur.role.description,
                'assigned_at': ur.assigned_at.isoformat() if ur.assigned_at else None
            } for ur in user_roles]
        }), 200
    except Exception as e:
        logger.error(f"Error getting user roles: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@admin_api_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@token_required
@admin_required
def assign_role(user_id):
    """Assign a role to a user"""
    try:
        data = request.get_json()
        role_id = data.get('role_id')
        
        if not role_id:
            return jsonify({'message': 'role_id is required'}), 400
        
        # Check if user exists
        user = User.query.get_or_404(user_id)
        
        # Check if role exists
        role = Role.query.get_or_404(role_id)
        
        # Check if already assigned
        existing = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
        if existing:
            return jsonify({'message': 'Role already assigned to user'}), 400
        
        # Assign role
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.session.add(user_role)
        db.session.commit()
        
        logger.info(f"Role {role.name} assigned to user {user.email}")
        
        return jsonify({
            'message': 'Role assigned successfully',
            'user_id': user_id,
            'role_id': role_id
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error assigning role: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@admin_api_bp.route('/users/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
@token_required
@admin_required
def remove_role(user_id, role_id):
    """Remove a role from a user"""
    try:
        user_role = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first_or_404()
        db.session.delete(user_role)
        db.session.commit()
        
        logger.info(f"Role {role_id} removed from user {user_id}")
        
        return jsonify({'message': 'Role removed successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error removing role: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@admin_api_bp.route('/permissions', methods=['GET'])
@token_required
@admin_required
def get_permissions():
    """Get all permissions"""
    try:
        permissions = Permission.query.all()
        return jsonify({
            'permissions': [{
                'id': p.id,
                'resource': p.resource.name,
                'action': p.action.name
            } for p in permissions]
        }), 200
    except Exception as e:
        logger.error(f"Error getting permissions: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@admin_api_bp.route('/roles', methods=['GET'])
@token_required
@admin_required
def get_roles():
    """Get all roles"""
    try:
        roles = Role.query.all()
        return jsonify({
            'roles': [{
                'id': r.id,
                'name': r.name,
                'description': r.description
            } for r in roles]
        }), 200
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        return jsonify({'message': 'Internal server error'}), 500

@admin_api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'auth_system',
        'admin_api': 'running'
    }), 200
