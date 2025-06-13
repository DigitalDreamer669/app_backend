#!/bin/bash

# =================================================================
# РАСШИРЕННЫЙ СКРИПТ ДЛЯ ТЕСТИРОВАНИЯ API ЗАЯВОК
# =================================================================
#
# Этот скрипт выполняет полный цикл для НЕСКОЛЬКИХ наборов данных.

# --- Переменные ---
API_URL="http://localhost:8000"
# Убедитесь, что этот пользователь существует и имеет type_of_user = 'client'
LOGIN="updated_newtestuser"
PASSWORD="updated_simplepassword"
TOKEN=""

# --- МАССИВЫ С ТЕСТОВЫМИ ДАННЫМИ ---
DESCRIPTIONS=("Требуется гусеничный экскаватор для котлована" "Нужен автокран на 25 тонн для монтажных работ" "Аренда самосвала для вывоза грунта")
TYPES=("Экскаватор" "Автокран" "Самосвал")
CITIES=("Москва" "Санкт-Петербург" "Новосибирск")
PRICES=(55000 32000 18000)

# Количество тестовых прогонов (равно количеству элементов в массивах)
TEST_RUNS=${#DESCRIPTIONS[@]}

# --- Функции для вывода ---
function print_header() { echo ""; echo "================================================="; echo " $1"; echo "================================================="; }
function print_success() { echo "✅  $1"; }
function print_error() { echo "❌  $1"; if [ ! -z "$2" ]; then echo "   Ответ сервера: $2"; fi; exit 1; }


# =================================================================
# НАЧАЛО ТЕСТИРОВАНИЯ
# =================================================================

# --- ШАГ 1: АУТЕНТИФИКАЦИЯ (выполняется один раз) ---
print_header "ШАГ 1: Аутентификация для получения токена доступа"
TOKEN_RESPONSE=$(curl -s -X POST "${API_URL}/login" -H "Content-Type: application/json" -d "{\"username\": \"${LOGIN}\", \"password\": \"${PASSWORD}\"}")
TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r .token)
if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then print_error "Не удалось получить токен." "$TOKEN_RESPONSE"; else print_success "Токен доступа успешно получен."; fi


# --- ЦИКЛ ТЕСТИРОВАНИЯ ---
for (( i=0; i<$TEST_RUNS; i++ )); do
    # Переменные для текущего теста
    CURRENT_DESCRIPTION="${DESCRIPTIONS[$i]}"
    CURRENT_TYPE="${TYPES[$i]}"
    CURRENT_CITY="${CITIES[$i]}"
    CURRENT_PRICE=${PRICES[$i]}
    ANONYMOUS_ID=""
    APP_ID=""
    
    print_header "ЗАПУСК ТЕСТА #${i+1}: Тип техники - ${CURRENT_TYPE}"

    # --- ШАГ 2: РЕГИСТРАЦИЯ АНОНИМНОЙ СЕССИИ ---
    echo "--- Шаг 2: Регистрация анонимной сессии для теста #${i+1} ---"
    ANON_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/anonymous-sessions/register" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"device_info": {"user_agent": "cURL Test Script"}}')
    HTTP_CODE=$(echo "$ANON_RESPONSE" | tail -n1)
    BODY=$(echo "$ANON_RESPONSE" | sed '$d')
    if [ "$HTTP_CODE" -ne 201 ]; then print_error "Ошибка регистрации анонимной сессии. Код: $HTTP_CODE" "$BODY"; fi
    ANONYMOUS_ID=$(echo "$BODY" | jq -r .id)
    print_success "Анонимная сессия #${i+1} зарегистрирована. ID заказчика: $ANONYMOUS_ID"

    # --- ШАГ 3: СОЗДАНИЕ НОВОЙ ЗАЯВКИ ---
    echo "--- Шаг 3: Создание новой заявки #${i+1} ---"
    CREATE_PAYLOAD=$(printf '{"статус_заявки": "новая", "тип_техники": "%s", "описание": "%s", "город": "%s", "проходная_цена": %s, "id_заказчика": %s}' "$CURRENT_TYPE" "$CURRENT_DESCRIPTION" "$CURRENT_CITY" "$CURRENT_PRICE" "$ANONYMOUS_ID")
    CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/applications" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "$CREATE_PAYLOAD")
    HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
    BODY=$(echo "$CREATE_RESPONSE" | sed '$d')
    if [ "$HTTP_CODE" -ne 201 ]; then print_error "Ошибка создания заявки #${i+1}. Код: $HTTP_CODE" "$BODY"; fi
    APP_ID=$(echo "$BODY" | jq -r .id)
    print_success "Заявка #${i+1} успешно создана. ID заявки: $APP_ID"

    # --- ШАГ 4: ОБНОВЛЕНИЕ ЗАЯВКИ ---
    echo "--- Шаг 4: Обновление заявки #${i+1} ---"
    UPDATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "${API_URL}/applications/${APP_ID}" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -H "x-anonymous-user-id: ${ANONYMOUS_ID}" -d '{"статус_заявки": "в работе"}')
    HTTP_CODE=$(echo "$UPDATE_RESPONSE" | tail -n1)
    BODY=$(echo "$UPDATE_RESPONSE" | sed '$d')
    if [ "$HTTP_CODE" -ne 200 ]; then print_error "Ошибка обновления заявки #${i+1}. Код: $HTTP_CODE" "$BODY"; fi
    print_success "Заявка ID: $APP_ID успешно обновлена."

    # --- ШАГ 5: УДАЛЕНИЕ ЗАЯВКИ ---
    echo "--- Шаг 5: Удаление заявки #${i+1} ---"
    DELETE_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${API_URL}/applications/${APP_ID}" -H "Authorization: Bearer $TOKEN" -H "x-anonymous-user-id: ${ANONYMOUS_ID}")
    if [ "$DELETE_CODE" -ne 204 ]; then print_error "Ошибка удаления заявки #${i+1}. Код ответа: $DELETE_CODE"; fi
    print_success "Заявка ID: $APP_ID успешно удалена."

done

print_header "Все тесты завершены успешно!"

