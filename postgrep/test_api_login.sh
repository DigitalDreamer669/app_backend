#!/bin/bash

# ==============================================================================
#  УЛУЧШЕННЫЙ ТЕСТОВЫЙ СКРИПТ API v2
#  - Генерирует уникальное имя пользователя для каждого запуска.
#  - Можно запускать многократно без ошибок о дубликатах.
#  - Добавлен шаг проверки получения созданного пользователя по ID.
# ==============================================================================

# --- Настройки ---
# Учетные данные администратора
ADMIN_USER="admin_user"
ADMIN_PASS='^pu8LPn:5{[+6;:)LaW|1ck' 

# ID существующего пользователя для теста на ОБНОВЛЕНИЕ
# Этот тест проверяет обновление старой записи, он не зависит от нового пользователя
EXISTING_USER_ID="9c81b7a3-c573-44f9-8fa0-70d052eb0657"

# --- Шаг 1: Генерация уникальных данных ---
TIMESTAMP=$(date +%s)
UNIQUE_USER="testuser_$TIMESTAMP"
UNIQUE_EMAIL="$UNIQUE_USER@example.com"
echo "✨ Будем создавать уникального пользователя: $UNIQUE_USER"


# --- Шаг 2: Вход и получение токена ---
echo -e "\n🔑 Попытка входа и получения токена..."

TOKEN=$(curl -s -X POST "http://localhost:8001/admin/login" \
-H "Content-Type: application/json" \
-d "{
  \"username\": \"$ADMIN_USER\",
  \"password\": \"$ADMIN_PASS\"
}" | jq -r .token)

# Проверяем, что токен получен
if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
    echo "❌ Ошибка: Не удалось получить токен. Проверьте логин/пароль и доступность сервера."
    exit 1
fi
echo "✅ Токен успешно получен и сохранен."


# --- Шаг 3: Создание НОВОГО УНИКАЛЬНОГО пользователя ---
echo -e "\n➕ Создание нового пользователя '$UNIQUE_USER'..."
NEW_USER_RESPONSE=$(curl -s -X POST "http://localhost:8001/admin/users" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d "{
    \"username\": \"$UNIQUE_USER\",
    \"password\": \"new_strong_password\",
    \"email\": \"$UNIQUE_EMAIL\",
    \"type_of_user\": \"dynamic_tester\"
}")

echo "$NEW_USER_RESPONSE" | jq .
NEW_USER_ID=$(echo "$NEW_USER_RESPONSE" | jq -r .id)


# --- Шаг 4: Проверка, что пользователь действительно создался (по ID) ---
if [ -n "$NEW_USER_ID" ] && [ "$NEW_USER_ID" != "null" ]; then
    echo -e "\n🔎 Проверка получения созданного пользователя по ID: $NEW_USER_ID..."
    curl -s -X GET "http://localhost:8001/admin/users/$NEW_USER_ID" \
    -H "Authorization: Bearer $TOKEN" | jq .
else
    echo "⚠️ Не удалось создать пользователя, дальнейшие тесты с ним пропускаются."
fi


# --- Шаг 5: Обновление ДРУГОГО, СУЩЕСТВУЮЩЕГО пользователя ---
echo -e "\n🔄 Обновление старого пользователя с ID: $EXISTING_USER_ID..."
curl -s -X PUT "http://localhost:8001/admin/users/$EXISTING_USER_ID" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d '{
    "type_of_user": "updated_owner"
}' | jq .


# --- Шаг 6: Удаление СОЗДАННОГО пользователя ---
if [ -n "$NEW_USER_ID" ] && [ "$NEW_USER_ID" != "null" ]; then
    echo -e "\n🗑️ Удаление созданного пользователя с ID: $NEW_USER_ID..."
    # Используем -v для вывода статус-кода
    curl -s -o /dev/null -w "HTTP статус: %{http_code}\n" -X DELETE "http://localhost:8001/admin/users/$NEW_USER_ID" \
    -H "Authorization: Bearer $TOKEN"
    echo "(Ожидаемый статус ответа: 204)"
else
    echo -e "\n🗑️ Пропуск удаления, так как пользователь не был создан."
fi


# --- Шаг 7: Выход из системы ---
echo -e "\n🚪 Выход из системы (Logout)..."
curl -s -X POST "http://localhost:8001/admin/logout" \
-H "Authorization: Bearer $TOKEN" | jq .


# --- Шаг 8: Проверка недействительности токена ---
echo -e "\n❌ Попытка доступа с недействительным токеном..."
curl -s -X GET "http://localhost:8001/admin/users" \
-H "Authorization: Bearer $TOKEN" | jq .

echo -e "\n🎉 Тестирование завершено."