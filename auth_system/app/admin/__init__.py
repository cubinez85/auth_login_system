"""
Admin package for Auth System

Этот модуль инициализирует и настраивает Flask-Admin панель управления
для системы аутентификации и авторизации.

Компоненты:
    - Flask-Admin инициализация
    - Регистрация ModelView для всех моделей БД
    - Кастомные view для тестирования аутентификации
    - Управление blacklist токенов
    - Helper функции для шаблонов

Использование:
    from app.admin import setup_admin
    admin = Admin(...)
    setup_admin(admin, db)

Автор: Auth System Team
Версия: 1.0.0
"""

from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for

# Импортируем функции и view из views.py
from app.admin.views import (
    setup_admin,
    add_admin_views,
    MyAdminIndexView,
    AdminSecureView,
    UserAdminView,
    RoleAdminView,
    ResourceAdminView,
    ActionAdminView,
    PermissionAdminView,
    UserRoleAdminView,
    UserPermissionAdminView,
    AuthTestView,
    TokenBlacklistView,
    # Helper functions для шаблонов
    count_users,
    count_roles,
    count_permissions,
    count_blacklisted_tokens,
)

# =============================================================================
# Публичный API пакета
# =============================================================================
__all__ = [
    # Основные функции инициализации
    'setup_admin',
    'add_admin_views',
    
    # Flask-Admin базовые классы
    'Admin',
    'ModelView',
    'BaseView',
    'expose',
    
    # Кастомные View классы
    'MyAdminIndexView',
    'AdminSecureView',
    'UserAdminView',
    'RoleAdminView',
    'ResourceAdminView',
    'ActionAdminView',
    'PermissionAdminView',
    'UserRoleAdminView',
    'UserPermissionAdminView',
    'AuthTestView',
    'TokenBlacklistView',
    
    # Helper функции для шаблонов (context processor)
    'count_users',
    'count_roles',
    'count_permissions',
    'count_blacklisted_tokens',
]


# =============================================================================
# Альтернативная функция инициализации (для гибкости)
# =============================================================================
def init_admin(app, db, admin_instance=None):
    """
    Инициализация админ-панели с приложением Flask
    
    Args:
        app: Flask приложение
        db: SQLAlchemy instance
        admin_instance: Существующий Admin instance (опционально)
    
    Returns:
        Admin instance
    
    Example:
        from app.admin import init_admin
        admin = init_admin(app, db)
    """
    if admin_instance is None:
        admin_instance = Admin(
            app,
            name='Auth System Admin',
            template_mode='bootstrap4',
            index_view=MyAdminIndexView(
                template='admin/index.html',
                name='Dashboard',
                url='/admin/'
            ),
            base_template='admin/master.html'
        )
    
    # Настройка view
    setup_admin(admin_instance, db)
    
    return admin_instance


# =============================================================================
# Helper для регистрации context processor в Flask app
# =============================================================================
def register_context_processors(app):
    """
    Регистрация helper функций как context processors для шаблонов
    
    Args:
        app: Flask приложение
    
    Example:
        from app.admin import register_context_processors
        register_context_processors(app)
    """
    @app.context_processor
    def inject_admin_counts():
        """Добавляет счётки в контекст всех шаблонов"""
        try:
            return dict(
                count_users=count_users,
                count_roles=count_roles,
                count_permissions=count_permissions,
                count_blacklisted_tokens=count_blacklisted_tokens,
            )
        except Exception as e:
            # Возвращаем безопасные значения при ошибке БД
            return dict(
                count_users=lambda: 0,
                count_roles=lambda: 0,
                count_permissions=lambda: 0,
                count_blacklisted_tokens=lambda: 0,
            )
    
    return app


# =============================================================================
# Конфигурация по умолчанию для ModelView
# =============================================================================
class SecureModelView(ModelView):
    """
    Базовый ModelView с настройками безопасности по умолчанию
    
    Наследуйте от этого класса для создания своих view с едиными
    настройками безопасности и оформления.
    """
    
    # Пагинация
    page_size = 20
    can_set_page_size = True
    
    # Поиск и фильтры
    can_search = True
    filter_bar = True
    
    # Операции
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    can_export = True
    
    # Оформление
    column_display_actions = True
    column_display_pk = True
    
    def is_accessible(self):
        """
        Проверка доступа к view
        
        TODO: Заменить на реальную проверку через Flask-Login в продакшене:
        return current_user.is_authenticated and current_user.is_superuser
        """
        return True
    
    def inaccessible_callback(self, name, **kwargs):
        """Перенаправление при отсутствии доступа"""
        return redirect(url_for('admin.index'))


# =============================================================================
# Утилиты для работы с админкой
# =============================================================================
def get_admin_url(endpoint, **kwargs):
    """
    Генерация URL для admin endpoint
    
    Args:
        endpoint: Имя endpoint (например, 'user.index')
        **kwargs: Параметры для URL
    
    Returns:
        str: Полный URL
    
    Example:
        url = get_admin_url('user.index')
        url = get_admin_url('user.edit', id=1)
    """
    return url_for(f'admin.{endpoint}', **kwargs)


def get_model_view(model_class, admin_instance, db_session):
    """
    Получение или создание ModelView для модели
    
    Args:
        model_class: Класс модели SQLAlchemy
        admin_instance: Admin instance
        db_session: SQLAlchemy session
    
    Returns:
        ModelView instance
    """
    view_class = type(
        f'{model_class.__name__}View',
        (SecureModelView,),
        {}
    )
    return view_class(model_class, db_session)


# =============================================================================
# Логирование действий в админке (опционально)
# =============================================================================
def log_admin_action(user, action, model_name, record_id=None, details=None):
    """
    Логирование действий администратора
    
    Args:
        user: Пользователь, выполнивший действие
        action: Тип действия ('create', 'edit', 'delete', 'view')
        model_name: Имя модели
        record_id: ID записи (опционально)
        details: Дополнительные детали (dict, опционально)
    
    TODO: Реализовать сохранение в таблицу audit_logs
    """
    import logging
    logger = logging.getLogger('admin.audit')
    
    log_message = (
        f"[ADMIN ACTION] User: {user}, "
        f"Action: {action}, "
        f"Model: {model_name}, "
        f"Record ID: {record_id}"
    )
    
    if details:
        log_message += f", Details: {details}"
    
    logger.info(log_message)


# =============================================================================
# Проверка целостности админки при старте
# =============================================================================
def verify_admin_setup(admin_instance, db):
    """
    Проверка корректности настройки админки
    
    Args:
        admin_instance: Admin instance
        db: SQLAlchemy instance
    
    Returns:
        dict: Результат проверки с ошибками (если есть)
    """
    errors = []
    warnings = []
    
    # Проверка наличия обязательных view
    required_views = ['user', 'role', 'permission']
    registered_views = [view.endpoint for view in admin_instance._views]
    
    for view in required_views:
        if not any(view in v for v in registered_views):
            warnings.append(f"View '{view}' not found in registered views")
    
    # Проверка подключения к БД
    try:
        db.session.execute('SELECT 1')
    except Exception as e:
        errors.append(f"Database connection failed: {str(e)}")
    
    return {
        'ok': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'views_count': len(admin_instance._views),
    }
