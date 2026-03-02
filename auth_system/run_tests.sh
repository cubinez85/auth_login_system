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
