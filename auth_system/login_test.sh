#!/bin/bash
# login_test.sh

BASE_URL="http://localhost:8084"
EMAIL="cubinez85@cubinez.ru"
PASSWORD="xzSA1W_1P8"  # ← замените на ваш пароль

echo "=== Вход в систему ==="
RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

echo "$RESPONSE" | python3 -m json.tool

# Извлечение токена
ACCESS_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))")

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Ошибка входа"
    exit 1
fi

echo -e "\n✅ Успешный вход!"
echo "🔑 Access Token: ${ACCESS_TOKEN:0:60}..."

# Тест доступа к защищённому ресурсу
echo -e "\n=== Тест доступа к /api/projects/ ==="
curl -s -X GET "$BASE_URL/api/projects/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool

echo -e "\n=== Тест доступа к /api/reports/ (должно быть 403 для обычного пользователя) ==="
curl -s -w "\nHTTP: %{http_code}\n" -X GET "$BASE_URL/api/reports/" \
  -H "Authorization: Bearer $ACCESS_TOKEN" | head -5
