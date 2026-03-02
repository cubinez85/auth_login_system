"""
Admin Views для Auth System

Содержит:
- ModelView для управления моделями БД
- Кастомные BaseView для тестирования аутентификации
- Helper функции для шаблонов
"""

from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, AdminIndexView, expose
from flask import redirect, url_for, request, render_template, flash
from app import db
from app.models.user import User
from app.models.permission import (
    Resource, Action, Permission, Role,
    RolePermission, UserRole, UserPermission
)
from app.models.token import TokenBlacklist
from app.utils.jwt_helper import generate_tokens, blacklist_token, get_token_expires
import jwt
from datetime import datetime


# =============================================================================
# Кастомная главная страница админки
# =============================================================================
class MyAdminIndexView(AdminIndexView):
    """Кастомная индексная страница"""
    
    @expose('/')
    def index(self):
        return self.render('admin/index.html')


# =============================================================================
# Базовый безопасный View
# =============================================================================
class AdminSecureView(ModelView):
    """Базовый View с проверкой доступа"""
    
    def is_accessible(self):
        # TODO: В продакшене заменить на проверку Flask-Login
        # return current_user.is_authenticated and current_user.is_superuser
        return True
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.index'))


# =============================================================================
# Admin Views для моделей
# =============================================================================

class UserAdminView(AdminSecureView):
    """Управление пользователями"""
    column_list = ['id', 'email', 'last_name', 'first_name', 'is_active', 'is_superuser', 'created_at']
    column_searchable_list = ['email', 'last_name', 'first_name']
    column_filters = ['is_active', 'is_superuser']
    form_excluded_columns = ['password_hash', 'roles', 'permissions', 'deleted_at']
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    def delete_model(self, model):
        """Мягкое удаление вместо hard delete"""
        model.soft_delete()
        db.session.commit()
        return True


class RoleAdminView(AdminSecureView):
    """Управление ролями"""
    column_list = ['id', 'name', 'description']
    form_columns = ['name', 'description']
    can_create = True
    can_edit = True
    can_delete = True


class ResourceAdminView(AdminSecureView):
    """Управление ресурсами"""
    column_list = ['id', 'name', 'description']
    form_columns = ['name', 'description']
    can_create = True
    can_edit = True
    can_delete = True


class ActionAdminView(AdminSecureView):
    """Управление действиями"""
    column_list = ['id', 'name', 'description']
    form_columns = ['name', 'description']
    can_create = True
    can_edit = True
    can_delete = True


class PermissionAdminView(AdminSecureView):
    """Управление разрешениями"""
    column_list = ['id', 'resource', 'action']
    column_filters = ['resource_id', 'action_id']
    can_create = True
    can_edit = True
    can_delete = True


class RolePermissionAdminView(AdminSecureView):
    """Связь ролей и разрешений"""
    column_list = ['id', 'role', 'permission']
    column_filters = ['role_id', 'permission_id']
    form_columns = ['role', 'permission']
    can_create = True
    can_edit = True
    can_delete = True


class UserRoleAdminView(AdminSecureView):
    """Назначение ролей пользователям"""
    column_list = ['id', 'user', 'role', 'assigned_at']
    column_filters = ['user_id', 'role_id']
    form_columns = ['user', 'role']
    can_create = True
    can_edit = True
    can_delete = True


class UserPermissionAdminView(AdminSecureView):
    """Индивидуальные разрешения пользователей"""
    column_list = ['id', 'user', 'permission', 'granted', 'assigned_at']
    column_filters = ['user_id', 'permission_id', 'granted']
    form_columns = ['user', 'permission', 'granted']
    can_create = True
    can_edit = True
    can_delete = True


# =============================================================================
# 🔐 Auth Test View — тестирование аутентификации
# =============================================================================
class AuthTestView(BaseView):
    """Кастомная view для тестирования API аутентификации"""
    
    @expose('/')
    def index(self):
        """Страница тестирования auth API"""
        roles = Role.query.all()
        users = User.query.order_by(User.created_at.desc()).limit(20).all()
        return self.render('admin/auth_test.html',
                         roles=roles,
                         users=users,
                         now=datetime.utcnow().timestamp())
    
    @expose('/api-test/register', methods=['POST'])
    def api_test_register(self):
        """Тест регистрации через админку"""
        try:
            data = request.form
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            if not email or not password:
                flash('❌ Email и пароль обязательны', 'warning')
                return redirect(url_for('.index'))
            
            if User.query.filter_by(email=email).first():
                flash(f'⚠️ Пользователь {email} уже существует', 'warning')
                return redirect(url_for('.index'))
            
            user = User(
                email=email,
                last_name=data.get('last_name', 'Test'),
                first_name=data.get('first_name', 'User'),
                middle_name=data.get('middle_name', '')
            )
            user.password = password
            db.session.add(user)
            db.session.flush()
            
            role_id = data.get('role_id')
            if role_id:
                user_role = UserRole(user_id=user.id, role_id=int(role_id))
                db.session.add(user_role)
            
            db.session.commit()
            tokens = generate_tokens(user.id)
            
            flash(f'✅ Пользователь {email} создан. ID: {user.id}', 'success')
            return self.render('admin/auth_test.html',
                             roles=Role.query.all(),
                             users=User.query.order_by(User.created_at.desc()).limit(20).all(),
                             last_tokens=tokens,
                             last_user=user,
                             now=datetime.utcnow().timestamp())
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Ошибка: {str(e)}', 'danger')
            return redirect(url_for('.index'))
    
    @expose('/api-test/login', methods=['POST'])
    def api_test_login(self):
        """Тест входа через админку"""
        try:
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('❌ Email и пароль обязательны', 'warning')
                return redirect(url_for('.index'))
            
            user = User.query.filter_by(email=email, is_active=True).first()
            
            if not user or not user.verify_password(password):
                flash('❌ Неверные учётные данные', 'danger')
                return redirect(url_for('.index'))
            
            tokens = generate_tokens(user.id)
            
            flash(f'✅ Вход успешен для {email}', 'success')
            return self.render('admin/auth_test.html',
                             roles=Role.query.all(),
                             users=User.query.order_by(User.created_at.desc()).limit(20).all(),
                             last_tokens=tokens,
                             last_user=user,
                             now=datetime.utcnow().timestamp())
            
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'danger')
            return redirect(url_for('.index'))
    
    @expose('/api-test/blacklist', methods=['POST'])
    def api_test_blacklist(self):
        """Добавление токена в blacklist"""
        try:
            token = request.form.get('token', '').strip()
            if not token:
                flash('❌ Токен не указан', 'warning')
                return redirect(url_for('.index'))
            
            expires_at = get_token_expires(token)
            if blacklist_token(token, expires_at):
                flash('✅ Токен добавлен в blacklist', 'success')
            else:
                flash('⚠️ Токен уже в blacklist', 'info')
            
            return redirect(url_for('.index'))
            
        except Exception as e:
            flash(f'❌ Ошибка: {str(e)}', 'danger')
            return redirect(url_for('.index'))
    
    @expose('/api-test/decode', methods=['POST'])
    def api_test_decode(self):
        """Декодирование токена для отладки"""
        try:
            token = request.form.get('token', '').strip()
            if not token:
                flash('❌ Токен не указан', 'warning')
                return redirect(url_for('.index'))
            
            payload = jwt.decode(token, options={"verify_signature": False})
            is_blacklisted = TokenBlacklist.is_blacklisted(token)
            
            flash('✅ Токен декодирован', 'success')
            return self.render('admin/auth_test.html',
                             roles=Role.query.all(),
                             users=User.query.order_by(User.created_at.desc()).limit(20).all(),
                             decoded_payload=payload,
                             decoded_token=token,
                             is_blacklisted=is_blacklisted,
                             now=datetime.utcnow().timestamp())
            
        except jwt.ExpiredSignatureError:
            flash('⚠️ Токен истёк', 'warning')
            return redirect(url_for('.index'))
        except jwt.InvalidTokenError as e:
            flash(f'❌ Неверный токен: {str(e)}', 'danger')
            return redirect(url_for('.index'))
        except Exception as e:
            flash(f'❌ Ошибка декодирования: {str(e)}', 'danger')
            return redirect(url_for('.index'))


# =============================================================================
# 🚫 Token Blacklist View — управление отозванными токенами
# =============================================================================
class TokenBlacklistView(BaseView):
    """Просмотр и управление blacklist токенов"""
    
    @expose('/')
    def index(self):
        tokens = TokenBlacklist.query\
            .order_by(TokenBlacklist.blacklisted_on.desc())\
            .limit(100).all()
        return self.render('admin/token_blacklist.html',
                         tokens=tokens,
                         now=datetime.utcnow())
    
    @expose('/clear-expired', methods=['POST'])
    def clear_expired(self):
        """Удаление истёкших токенов из blacklist"""
        try:
            deleted = TokenBlacklist.query.filter(
                TokenBlacklist.expires_at < datetime.utcnow()
            ).delete(synchronize_session=False)
            db.session.commit()
            flash(f'✅ Удалено {deleted} истёкших токенов', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Ошибка: {str(e)}', 'danger')
        return redirect(url_for('.index'))


# =============================================================================
# Функция настройки админки
# =============================================================================
def setup_admin(admin_instance, db_instance):
    """Регистрация всех admin views"""
    
    # Кастомные view
    admin_instance.add_view(AuthTestView(
        name='🔐 Auth Test',
        category='🧪 Testing',
        endpoint='auth_test'
    ))
    admin_instance.add_view(TokenBlacklistView(
        name='🚫 Token Blacklist',
        category='🔒 Security',
        endpoint='token_blacklist'
    ))
    
    # User Management
    admin_instance.add_view(UserAdminView(
        User, db_instance.session,
        name='👥 Users',
        category='👤 User Management'
    ))
    
    # Access Control (RBAC)
    admin_instance.add_view(RoleAdminView(
        Role, db_instance.session,
        name='🎭 Roles',
        category='🔐 Access Control'
    ))
    admin_instance.add_view(ResourceAdminView(
        Resource, db_instance.session,
        name='📦 Resources',
        category='🔐 Access Control'
    ))
    admin_instance.add_view(ActionAdminView(
        Action, db_instance.session,
        name='⚡ Actions',
        category='🔐 Access Control'
    ))
    admin_instance.add_view(PermissionAdminView(
        Permission, db_instance.session,
        name='🔑 Permissions',
        category='🔐 Access Control'
    ))
    admin_instance.add_view(UserRoleAdminView(
        UserRole, db_instance.session,
        name='👤→🎭 User Roles',
        category='🔐 Access Control'
    ))
    admin_instance.add_view(RolePermissionAdminView(
        RolePermission, db_instance.session,
        name='🎭→🔑 Role Permissions',
        category='🔐 Access Control'
    ))
    admin_instance.add_view(UserPermissionAdminView(
        UserPermission, db_instance.session,
        name='👤→🔑 User Permissions',
        category='🔐 Access Control'
    ))
    
    print("✅ Admin views configured successfully")
    return admin_instance


# Для обратной совместимости
add_admin_views = setup_admin


# =============================================================================
# Helper функции для шаблонов (context processor)
# =============================================================================
def count_users():
    """Количество активных пользователей"""
    try:
        return User.query.filter_by(is_active=True).count()
    except:
        return 0

def count_roles():
    """Количество ролей"""
    try:
        return Role.query.count()
    except:
        return 0

def count_permissions():
    """Количество разрешений"""
    try:
        return Permission.query.count()
    except:
        return 0

def count_blacklisted_tokens():
    """Количество активных токенов в blacklist"""
    try:
        return TokenBlacklist.query.filter(
            TokenBlacklist.expires_at > datetime.utcnow()
        ).count()
    except:
        return 0
