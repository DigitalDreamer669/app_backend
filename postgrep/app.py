# app.py
from fastapi import FastAPI, HTTPException
import os
import psycopg2
import psycopg2.extras
from psycopg2.extras import Json
from dotenv import load_dotenv
from typing import Optional, Dict, Any 
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

def get_db_connection():
    try:
        # Получаем значения из переменных окружения
        # Имена переменных здесь должны точно соответствовать тем, что вы указали в файле .env
        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")

        # Добавим проверки, чтобы убедиться, что переменные были загружены
        if not all([db_host, db_name, db_user, db_password]):
            missing_vars = []
            if not db_host: missing_vars.append("DB_HOST")
            if not db_name: missing_vars.append("DB_NAME")
            if not db_user: missing_vars.append("DB_USER")
            if not db_password: missing_vars.append("DB_PASSWORD")
            
            error_msg = f"Ошибка: Отсутствуют необходимые переменные окружения для подключения к БД: {', '.join(missing_vars)}. Убедитесь, что файл .env существует и содержит все переменные."
            print(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        print(f"Попытка подключения с использованием переменных окружения:")
        print(f"  Хост: {db_host}")
        print(f"  База данных: {db_name}")
        print(f"  Пользователь: {db_user}")
        # print(f"  Пароль: {db_password}") # Не печатайте пароли в реальном коде!

        conn = psycopg2.connect(
            host=db_host,
            port=5432,                  # Порт PostgreSQL, обычно 5432
            database=db_name,
            user=db_user,
            password=db_password
        )
        print("Успешное подключение к базе данных через .env!")
        return conn
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
        # Перевыбрасываем как HTTPException для обработки FastAPI
        raise HTTPException(status_code=500, detail=f"Не удалось подключиться к базе данных: {e}")

# вывод данных
@app.get("/suppliers_view")
async def get_suppliers_view_data():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Ensure schema and view names are correctly quoted if they contain non-standard characters
        cur.execute('SELECT * FROM "поставщики"."представление_поставщики"')
        column_names = [desc[0] for desc in cur.description]
        data = cur.fetchall()
        
        # Convert data to a list of dictionaries
        result = []
        for row in data:
            result.append(dict(zip(column_names, row)))
        
        return {"data": result}
    except HTTPException:
        raise # Re-raise HTTPException as it's already handled
    except Exception as e:
        print(f"Error fetching data: {e}")
        raise HTTPException(status_code=500, detail="Error fetching data from view")
    finally:
        if conn:
            conn.close()







# Модель для создания нового поставщика (для POST запроса)
class SupplierCreate(BaseModel):
    наименование_юр_лица: str
    номер_телефона: Optional[str] = None
    телеграм_id: Optional[str] = None
    наименование_техники: str
    параметры_техники: Optional[Dict[str, Any]] = None

# Модель для обновления данных поставщика (для PUT запроса)
class SupplierUpdate(BaseModel):
    наименование_юр_лица: Optional[str] = None
    номер_телефона: Optional[str] = None
    телеграм_id: Optional[str] = None
    наименование_техники: Optional[str] = None
    параметры_техники: Optional[Dict[str, Any]] = None








# ЭНДПОИНТ: Для добавления данных поставщика (POST)
@app.post("/поставщики/")
async def create_supplier_data(supplier_data: SupplierCreate):
    conn = None
    print(f"Endpoint '/поставщики/' (POST) accessed with data: {supplier_data.dict()}")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        columns = []
        placeholders = []
        params = {}

        for field, value in supplier_data.dict().items():
            columns.append(f'"{field}"')
            placeholders.append(f'%({field})s')
            
            # *** КЛЮЧЕВОЕ ИЗМЕНЕНИЕ ЗДЕСЬ: Явное использование Json() ***
            if field == 'параметры_техники' and value is not None:
                params[field] = Json(value) # Оборачиваем словарь в Json()
            else:
                params[field] = value
        # **********************************************************

        query = f'INSERT INTO "поставщики"."поставщики" ({", ".join(columns)}) VALUES ({", ".join(placeholders)}) RETURNING *;'
        
        print(f"Executing insert query: {query} with params: {params}")
        cur.execute(query, params)
        new_row = cur.fetchone()
        conn.commit()

        if not new_row:
            raise HTTPException(status_code=500, detail="Не удалось создать поставщика.")

        column_names = [desc[0] for desc in cur.description]
        created_data = dict(zip(column_names, new_row))
        
        if 'id' in created_data and isinstance(created_data['id'], UUID):
            created_data['id'] = str(created_data['id'])
        for key, value in created_data.items():
            if isinstance(value, datetime):
                created_data[key] = value.isoformat()

        print(f"Supplier created with ID: {created_data.get('id')}")
        return {"message": "Поставщик успешно создан", "created_supplier": created_data}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR creating supplier: {e}")
        if hasattr(e, 'pgcode') and e.pgcode == '23505':
            raise HTTPException(status_code=409, detail=f"Ошибка данных: Запись с такими уникальными значениями уже существует. Детали: {e.pgerror}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании поставщика: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")









# ЭНДПОИНТ: Для обновления данных поставщика
@app.put("/поставщики/{supplier_id}")
async def update_supplier_data(supplier_id: UUID, supplier_update: SupplierUpdate):
    conn = None
    print(f"Endpoint '/поставщики/{supplier_id}' (PUT) accessed with data: {supplier_update.dict()}")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        set_clauses = []
        params = {}
        
        for field, value in supplier_update.dict(exclude_unset=True).items():
            set_clauses.append(f'"{field}" = %({field})s')
            
            # *** КЛЮЧЕВОЕ ИЗМЕНЕНИЕ ЗДЕСЬ: Явное использование Json() ***
            if field == 'параметры_техники' and value is not None:
                params[field] = Json(value) # Оборачиваем словарь в Json()
            else:
                params[field] = value
        # **********************************************************

        if not set_clauses:
            raise HTTPException(status_code=400, detail="No fields provided for update.")

        query = f'UPDATE "поставщики"."поставщики" SET {", ".join(set_clauses)} WHERE id = %(id)s RETURNING *;'
        params['id'] = str(supplier_id)

        print(f"Executing update query: {query} with params: {params}")
        cur.execute(query, params)
        updated_row = cur.fetchone()
        conn.commit()

        if not updated_row:
            raise HTTPException(status_code=404, detail=f"Поставщик с ID {supplier_id} не найден.")

        column_names = [desc[0] for desc in cur.description]
        updated_data = dict(zip(column_names, updated_row))
        
        if 'id' in updated_data and isinstance(updated_data['id'], UUID):
            updated_data['id'] = str(updated_data['id'])
        for key, value in updated_data.items():
            if isinstance(value, datetime):
                updated_data[key] = value.isoformat()

        print(f"Supplier {supplier_id} updated successfully.")
        return {"message": "Данные поставщика успешно обновлены", "updated_supplier": updated_data}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR updating supplier {supplier_id}: {e}")
        if hasattr(e, 'pgcode') and e.pgcode == '23505':
            raise HTTPException(status_code=409, detail=f"Ошибка данных: Запись с такими уникальными значениями уже существует. Детали: {e.pgerror}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении данных поставщика: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")







# ЭНДПОИНТ: Для удаления данных поставщика
@app.delete("/поставщики/{supplier_id}")
async def delete_supplier_data(supplier_id: UUID):
    conn = None
    print(f"Endpoint '/поставщики/{supplier_id}' (DELETE) accessed.")
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        query = 'DELETE FROM "поставщики"."поставщики" WHERE id = %s RETURNING id;'
        print(f"Executing delete query: {query} with ID: {supplier_id}")
        cur.execute(query, (str(supplier_id),))
        deleted_id = cur.fetchone()
        conn.commit()

        if not deleted_id:
            raise HTTPException(status_code=404, detail=f"Поставщик с ID {supplier_id} не найден.")

        print(f"Supplier {supplier_id} deleted successfully.")
        return {"message": f"Поставщик с ID {supplier_id} успешно удален."}
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR deleting supplier {supplier_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении данных поставщика: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

@app.get("/")
async def root():
    return {"message": "Welcome to the Suppliers API! Try /suppliers_view to get data."}
