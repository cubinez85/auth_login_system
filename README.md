production-ready backend-приложение на Flask с собственной реализацией системы аутентификации и авторизации,
не полагается полностью на встроенные механизмы фреймворков. 
Система включает гибкое разграничение доступа на основе ролей (RBAC), 
JWT-токены с механизмом отзыва, Flask-Admin панель для управления и полноценное API.

📧 Email Verification
Система подтверждения email при регистрации обеспечивает безопасность и валидацию учётных записей пользователей.

🔐 Как это работает
1. Регистрация → пользователь создаётся со статусом is_verified=False
2. Генерация токена → криптографически стойкий токен (24 часа)
3. Отправка письма → ссылка /api/auth/verify-email/{token}
4. Подтверждение → пользователь кликает ссылку → is_verified=True, is_active=True
5. Вход → только после верификации выдаются JWT-токены

# Тест на открытый релей 
telnet 95.174.94.246 25

EHLO test.cubinez.ru

MAIL FROM:<cubinez85@cubinez.ru>

RCPT TO:<cubinez85@gmail.com>


#Важно!!!
если проект развернут на wsl:
ip динамический - следить за изменением ip (check_ip.bat on Decktop)
при изменении ip - на почтовом сервере в /etc/postfix/main.cf in mynetworks = 127.0.0.0/8, 213.87.162.194<= заменить
если проект развернут на Cloud.ru с белым ip - в /etc/postfix/main.cf in mynetworks внести белый ip

🏗️ Технологический стек
Компонент
Технология
Backend
Python 3.10+ / Flask 2.3+
База данных
PostgreSQL 14+
ORM
SQLAlchemy + Flask-SQLAlchemy
Миграции
Flask-Migrate (Alembic)
Аутентификация
JWT (PyJWT) с собственной реализацией
Авторизация
RBAC (Role-Based Access Control)
Админ-панель
Flask-Admin (Bootstrap 4)
Безопасность
Werkzeug (password hashing), Flask-Limiter
CORS
Flask-CORS
Сервер
Gunicorn + Nginx
Документация
OpenAPI/Swagger (опционально: Flask-RESTX)

🔐 Система аутентификации
Эндпоинты
Метод
Endpoint
Описание
Доступ
POST
/api/auth/register/
Регистрация нового пользователя
Public
POST
/api/auth/login/
Вход, выдача JWT токенов
Public
POST
/api/auth/logout/
Выход, инвалидация токена (blacklist)
Authenticated
POST
/api/auth/refresh/
Обновление access токена через refresh
Authenticated
PUT
/api/auth/profile/
Обновление профиля (имя, фамилия, отчество)
Authenticated
DELETE
/api/auth/profile/
Мягкое удаление аккаунта (is_active=False)

Требования к безопасности
✅ Пароли: мин. 8 символов, заглавные + строчные буквы + цифры
✅ Хеширование: Werkzeug (generate_password_hash, check_password_hash)
✅ JWT Access Token: 15 минут (настраивается в .env)
✅ JWT Refresh Token: 7 дней (настраивается в .env)
✅ Blacklist: отозванные токены хранятся в БД (token_blacklist)
✅ Мягкое удаление: is_active=False, deleted_at=timestamp
✅ Rate Limiting: 5 регистраций/час, 10 входов/минуту

🛡️ Система авторизации (RBAC)
Модели данных

┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Resource   │────<│  Permission  │>────│   Action    │
│  (projects) │     │(projects:read)│    │   (read)    │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────┴───────┐
                    │              │
             ┌──────▼──────┐ ┌────▼─────────┐
             │RolePermission│ │UserPermission│
             └──────┬──────┘ └────┬─────────┘
                    │              │
             ┌──────▼──────┐ ┌────▼─────────┐
             │    Role     │ │     User     │
             │   (Admin)   │ │ (user@email) │
             └──────┬──────┘ └────┬─────────┘
                    │              │
                    └──────┬───────┘
                           │
                    ┌──────▼──────┐
                    │  UserRole   │
                    └─────────────┘
Сущности
Модель
Описание
Поля
Resource
Ресурсы системы
id, name (projects, documents), description
Action
Действия
id, name (create, read, update, delete), description
Permission
Разрешение (Resource + Action)
id, resource_id, action_id, уникальный составной ключ
Role
Роль пользователя
id, name (Admin, Manager, User), description, is_system
UserRole
Назначение роли пользователю
id, user_id, role_id, assigned_at
RolePermission
Разрешения роли
id, role_id, permission_id
UserPermission
Индивидуальные права (override)
id, user_id, permission_id, granted, expires_at
TokenBlacklist
Отозванные токены
id, token, blacklisted_on, expires_at

Логика проверки прав
1. Суперпользователь (is_superuser=True) → всегда разрешено
2. UserPermission (индивидуальное) → приоритет над ролью
3. RolePermission (через роль) → стандартная проверка
4. По умолчанию → запрет (403 Forbidden)

Декораторы
@token_required                    # Требует валидный JWT токен
@permission_required('projects', 'create')  # Требует право projects:create
@admin_required                    # Требует роль Admin или is_superuser

🧪 Mock-ресурсы для демонстрации
Endpoint
Метод
Доступ
Описание
/api/projects/
GET
Все аутентифицированные
Список проектов
/api/projects/
POST
Admin, Manager
Создание проекта
/api/projects/<id>/
GET
Admin или владелец
Детали проекта
/api/projects/<id>/
PUT
Admin или владелец
Редактирование
/api/projects/<id>/
DELETE
Только Admin
Удаление
/api/documents/
GET
Все аутентифицированные
Список документов
/api/reports/
GET
Только Admin
Отчёты (Admin only)
/api/health/
GET
Public
Проверка доступности API

🎛️ Flask-Admin панель
Разделы админки
🔐 Auth System Admin
├── 📊 Dashboard                      # Главная со статистикой
├── 🧪 Testing
│   └── 🔐 Auth Test                  # Тестирование регистрации/входа/JWT
├── 👤 User Management
│   └── 👥 Users                      # Управление пользователями
├── 🔐 Access Control (RBAC)
│   ├── 🎭 Roles                      # Роли
│   ├── 📦 Resources                  # Ресурсы
│   ├── ⚡ Actions                    # Действия
│   ├── 🔑 Permissions                # Разрешения
│   ├── 👤→🎭 User Roles              # Назначение ролей
│   ├── 🎭→🔑 Role Permissions        # Права ролей
│   └── 👤→🔑 User Permissions        # Индивидуальные права
└── 🔒 Security
    ├── 🚫 Token Blacklist            # Управление отозванными токенами
    └── 🗑️ Blacklist (Model)         # Просмотр таблицы blacklist

Функционал Auth Test View
📝 Регистрация: создание пользователя с назначением роли
🔑 Вход: генерация JWT токенов для тестирования
🎫 Просмотр токенов: копирование access/refresh токенов
🔍 Декодирование JWT: просмотр payload токена
🚫 Blacklist: принудительная инвалидация токена

🧪 Тестирование
Проверка аутентификации
# Регистрация
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!","confirm_password":"TestPass123!",
   "last_name":"Test","first_name":"User"}'

# Вход
curl -X POST http://127.0.0.1:8084/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass123!"}'

# Доступ к ресурсу с токеном
curl -X GET http://127.0.0.1:8084/api/projects/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"

# Logout (blacklist токена)
curl -X POST http://127.0.0.1:8084/api/auth/logout/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
(venv) cubinez85@cubinez:/var/www/auth_system$ cat run_tests.sh
#!/bin/bash
# =============================================================================
# run_tests.sh - Скрипт для запуска тестов Auth System
# =============================================================================
# Использование:
#   ./run_tests.sh              # Запустить все тесты
#   ./run_tests.sh verbose      # Запустить с подробным выводом
#   ./run_tests.sh coverage     # Запустить с отчётом о покрытии
#   ./run_tests.sh clean        # Очистить кэш pytest и coverage
#   ./run_tests.sh help         # Показать справку
# =============================================================================

set -e  # Выход при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Пути
PROJECT_ROOT="/var/www/auth_system"
VENV_PATH="${PROJECT_ROOT}/venv"
TESTS_DIR="${PROJECT_ROOT}/tests"
COVERAGE_DIR="${PROJECT_ROOT}/htmlcov"

# =============================================================================
# Функции
# =============================================================================

print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Виртуальное окружение не найдено: $VENV_PATH"
        print_warning "Создайте: python3 -m venv $VENV_PATH"
        exit 1
    fi
}

check_dependencies() {
    if ! python -c "import pytest" 2>/dev/null; then
        print_error "pytest не установлен"
        print_warning "Установите: pip install pytest pytest-cov"
        exit 1
    fi
}

verify_config() {
    print_header "1. Проверка конфигурации"
    python -c "from config import TestingConfig; print('Testing:', TestingConfig.TESTING)"
    python -c "from config import TestingConfig; print('DB URI:', TestingConfig.SQLALCHEMY_DATABASE_URI)"
    python -c "from config import TestingConfig; print('Engine Options:', TestingConfig.SQLALCHEMY_ENGINE_OPTIONS)"
    print_success "Конфигурация проверена"
}

run_tests() {
    print_header "2. Запуск тестов"

    if [ "$1" == "verbose" ]; then
        PYTHONPATH=$PROJECT_ROOT python -m pytest tests/ -v --tb=long
    else
        PYTHONPATH=$PROJECT_ROOT python -m pytest tests/ -v
    fi

    if [ $? -eq 0 ]; then
        print_success "Все тесты пройдены!"
    else
        print_error "Некоторые тесты не пройдены"
        exit 1
    fi
}

run_coverage() {
    print_header "3. Запуск тестов с покрытием"

    PYTHONPATH=$PROJECT_ROOT python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

    if [ $? -eq 0 ]; then
        print_success "Отчёт о покрытии создан: $COVERAGE_DIR/index.html"
        print_warning "Откройте в браузере: firefox $COVERAGE_DIR/index.html"
    else
        print_error "Тесты не пройдены"
        exit 1
    fi
}

clean_cache() {
    print_header "4. Очистка кэша"

    rm -rf .pytest_cache
    rm -rf .coverage
    rm -rf $COVERAGE_DIR
    rm -rf __pycache__
    rm -rf app/__pycache__
    rm -rf app/*/__pycache__
    rm -rf tests/__pycache__

    print_success "Кэш очищен"
}

show_help() {
    echo "Auth System Test Runner"
    echo ""
    echo "Использование:"
    echo "  ./run_tests.sh              Запустить все тесты"
    echo "  ./run_tests.sh verbose      Запустить с подробным выводом"
    echo "  ./run_tests.sh coverage     Запустить с отчётом о покрытии"
    echo "  ./run_tests.sh clean        Очистить кэш pytest и coverage"
    echo "  ./run_tests.sh help         Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  ./run_tests.sh"
    echo "  ./run_tests.sh coverage"
    echo "  ./run_tests.sh clean && ./run_tests.sh"
}

# =============================================================================
# Основная логика
# =============================================================================

cd "$PROJECT_ROOT"

# Активация venv
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    print_success "Виртуальное окружение активировано"
else
    check_venv
fi

# Проверка зависимостей
check_dependencies

# Обработка аргументов
case "${1:-}" in
    verbose)
        verify_config
        run_tests verbose
        ;;
    coverage)
        verify_config
        run_coverage
        ;;
    clean)
        clean_cache
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        verify_config
        run_tests
        ;;
    *)
        print_error "Неизвестная команда: $1"
        show_help
        exit 1
        ;;
esac

print_header "Готово!"

# Полезные команды 
sudo journalctl -u auth_system.service -n 50 --no-pager | grep -A5 "Traceback\|Error\|ImportError"

python -m py_compile app/admin/views.py && echo "✅ Syntax OK"

python -m py_compile app/__init__.py && echo "✅ __init__.py OK"

curl -I http://auth.cubinez.ru/admin/user/new/

sudo journalctl -u auth_system.service -n 100 --no-pager | grep -A10 -B5 "Error\|Traceback\|Exception"

python -c "from app import create_app; app = create_app('production'); print('✅ App OK')"

echo "=== Старые списки (теперь должны быть 302) ==="
for endpoint in user role resource action permission; do
    echo -n "/admin/$endpoint/ → "
    curl -s -o /dev/null -w "%{http_code} (Location: %{redirect_url})\n" http://auth.cubinez.ru/admin/$endpoint/
done

echo -e "\n=== Новые списки (должны быть 200) ==="
for endpoint in user_list role_list resource_list action_list permission_list; do
    echo -n "/admin/$endpoint/ → "
    curl -s -o /dev/null -w "%{http_code}\n" http://auth.cubinez.ru/admin/$endpoint/
done

# Инициализация базы данных
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

🔧 Дальнейшее развитие
Swagger/OpenAPI — авто-документация API (Flask-RESTX)
Email verification — подтверждение email при регистрации
2FA (TOTP) — двухфакторная аутентификация
Audit logs — логирование всех действий пользователей
Docker — контейнеризация для удобного деплоя
CI/CD — GitHub Actions / GitLab CI для автотестов и деплоя
Redis cache — кеширование частых запросов
WebSocket — real-time уведомления
