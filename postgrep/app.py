# app.py
import os
import logging
from typing import Optional, Dict, Any, List, Annotated
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from decimal import Decimal

import psycopg2
import psycopg2.extras
from psycopg2.extras import Json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

# 1. =================== НАСТРОЙКА И КОНФИГУРАЦИЯ ===================

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Unified Business Application")

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # В реальном проекте укажите домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Хранилище сессий в памяти ---
active_user_sessions = {}

# 2. =================== ПОДКЛЮЧЕНИЯ К БД ===================

def get_auth_db_connection():
    """Подключается к базе данных аутентификации."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST_login"),
            port=5432,
            database=os.getenv("DB_NAME_login"),
            user=os.getenv("DB_USER_login"),
            password=os.getenv("DB_PASSWORD_login")
        )
        return conn
    except Exception as e:
        logger.error(f"Auth DB connection error: {e}")
        raise HTTPException(status_code=503, detail="Сервис аутентификации недоступен.")

def get_main_db_connection():
    """Подключается к основной базе данных с заявками."""
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=5432,
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD")
        )
        return conn
    except Exception as e:
        logger.error(f"Main DB connection error: {e}")
        raise HTTPException(status_code=503, detail="Сервис данных недоступен.")

# 3. =================== МОДЕЛИ Pydantic ===================

# --- Модели для аутентификации ---
class UserLogin(BaseModel):
    username: str
    password: str

class UserPublicResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    is_active: bool

class UserLoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user_info: UserPublicResponse

# --- Модели для анонимных сессий ---
class AnonymousUserCreate(BaseModel):
    device_info: Optional[Dict[str, Any]] = None

class AnonymousUserOut(BaseModel):
    id: int # Возвращаем BIGINT ID
    наименование_юр_лица: str

# --- Модели для заявок ---
class ApplicationBase(BaseModel):
    статус_заявки: str
    описание: Optional[str] = None
    тип_техники: str
    город: Optional[str] = None
    срок_выполнения: Optional[datetime] = None
    проходная_цена: Optional[Decimal] = None

class ApplicationCreate(ApplicationBase):
    id_заказчика: int # Ожидаем INT ID от клиента

class ApplicationUpdate(BaseModel):
    статус_заявки: Optional[str] = None
    описание: Optional[str] = None
    тип_техники: Optional[str] = None
    город: Optional[str] = None
    срок_выполнения: Optional[datetime] = None
    проходная_цена: Optional[Decimal] = None

class ApplicationOut(ApplicationBase):
    id: int
    id_заказчика: int 
    лучшая_цена: Optional[Decimal] = None
    дата_создания: datetime
    дата_изменения: datetime
    наименование_заказчика: Optional[str] = None
    class Config: from_attributes = True

# 4. =================== ЛОГИКА АУТЕНТИФИКАЦИИ ===================

def cleanup_expired_user_sessions():
    """Удаляет просроченные сессии пользователей."""
    current_time = datetime.now()
    expired_tokens = [token for token, data in active_user_sessions.items() if data.get("expires", current_time) < current_time]
    for token in expired_tokens: active_user_sessions.pop(token, None)

async def verify_user_session(authorization: Annotated[str, Header()]):
    """Зависимость ("охранник") для проверки токена сессии пользователя."""
    cleanup_expired_user_sessions()
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer": raise HTTPException(status_code=401, detail="Неверная схема аутентификации")
        session_data = active_user_sessions.get(token)
        if not session_data or datetime.now() > session_data["expires"]: raise HTTPException(status_code=401, detail="Неверный или просроченный токен")
        return True
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Неверный формат заголовка Authorization")

# 5. =================== ЭНДПОИНТЫ API ===================

@app.post("/login", response_model=UserLoginResponse, tags=["Authentication"])
async def login_user(user_login: UserLogin):
    """Аутентифицирует пользователя и возвращает токен сессии."""
    conn = None
    try:
        conn = get_auth_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT * FROM "login_data"."login_data" WHERE username = %s;', (user_login.username,))
        user_record = cur.fetchone()

        if not user_record or user_record['password'] != user_record['password']: 
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        if user_record.get('type_of_user') != 'client':
            raise HTTPException(status_code=403, detail="Доступ для этого типа пользователя запрещен")
        if not user_record['is_active']:
            raise HTTPException(status_code=403, detail="Аккаунт неактивен")

        session_token = str(uuid4())
        expiration_time = datetime.now() + timedelta(hours=8)
        active_user_sessions[session_token] = {"user_id": user_record['id'], "expires": expiration_time}
        
        return UserLoginResponse(token=session_token, user_info=UserPublicResponse(**user_record))
    finally:
        if conn: conn.close()

@app.post("/anonymous-sessions/register", response_model=AnonymousUserOut, status_code=201, tags=["Anonymous Sessions"])
async def register_anonymous_session(anon_data: AnonymousUserCreate, _: bool = Depends(verify_user_session)):
    """Создает запись для анонимной сессии в 'юр_лица' и возвращает её BIGINT ID."""
    conn = None
    try:
        conn = get_main_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        anon_name = f"Анонимная сессия #{str(uuid4())[:8]}"
        temp_inn = int(datetime.now().timestamp() * 1000)

        query = """
            INSERT INTO main.юр_лица (наименование_юр_лица, инн, role, комментарии)
            VALUES (%s, %s, %s, %s) RETURNING id, "наименование_юр_лица";
        """
        cur.execute(query, (anon_name, temp_inn, 'client', Json(anon_data.device_info)))
        new_anonymous_user = cur.fetchone()
        conn.commit()
        return new_anonymous_user
    finally:
        if conn: conn.close()

@app.post("/applications", response_model=ApplicationOut, status_code=201, tags=["Applications"])
async def create_application(application_data: ApplicationCreate, _: bool = Depends(verify_user_session)):
    """Создает новую заявку, используя BIGINT ID заказчика."""
    conn = None
    try:
        conn = get_main_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        query = """
            INSERT INTO main.заявки (id_заказчика, статус_заявки, описание, тип_техники, город, срок_выполнения, проходная_цена)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *;
        """
        cur.execute(query, (
            application_data.id_заказчика, application_data.статус_заявки, application_data.описание,
            application_data.тип_техники, application_data.город, application_data.срок_выполнения,
            application_data.проходная_цена
        ))
        new_app = cur.fetchone()
        
        # ИСПРАВЛЕНИЕ: Добавляем второй запрос, чтобы получить 'наименование_заказчика'
        if new_app:
            cur.execute('SELECT "наименование_юр_лица" FROM main.юр_лица WHERE id = %s', (new_app['id_заказчика'],))
            company_info = cur.fetchone()
            new_app['наименование_заказчика'] = company_info['наименование_юр_лица'] if company_info else None

        conn.commit()
        return new_app
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Ошибка при создании заявки: {e}")
        raise HTTPException(status_code=500, detail="Не удалось создать заявку")
    finally:
        if conn: conn.close()

@app.get("/applications", response_model=List[ApplicationOut], tags=["Applications"])
async def get_all_applications(_: bool = Depends(verify_user_session), skip: int = 0, limit: int = 100):
    """Возвращает список всех заявок (требует аутентификации)."""
    conn = None
    try:
        conn = get_main_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # ИСПРАВЛЕНИЕ: Запрос теперь выбирает все нужные поля напрямую, а не через VIEW
        query = """
            SELECT
                z.id, z.статус_заявки, z.описание, z.тип_техники, z.город,
                z.срок_выполнения, z.проходная_цена, z.лучшая_цена, z.id_заказчика,
                yl.наименование_юр_лица AS "наименование_заказчика",
                z.дата_создания, z.дата_изменения
            FROM main.заявки z
            JOIN main.юр_лица yl ON z.id_заказчика = yl.id
            ORDER BY z.дата_создания DESC
            LIMIT %s OFFSET %s;
        """
        cur.execute(query, (limit, skip))
        return cur.fetchall()
    finally:
        if conn: conn.close()

@app.get("/applications/{application_id}", response_model=ApplicationOut, tags=["Applications"])
async def get_application_by_id(
    application_id: int,
    _: bool = Depends(verify_user_session)
):
    """Возвращает одну заявку по её ID."""
    conn = None
    try:
        conn = get_main_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # ИСПРАВЛЕНИЕ: Запрос теперь выбирает все нужные поля напрямую, а не через VIEW
        query = """
            SELECT
                z.id, z.статус_заявки, z.описание, z.тип_техники, z.город,
                z.срок_выполнения, z.проходная_цена, z.лучшая_цена, z.id_заказчика,
                yl.наименование_юр_лица AS "наименование_заказчика",
                z.дата_создания, z.дата_изменения
            FROM main.заявки z
            JOIN main.юр_лица yl ON z.id_заказчика = yl.id
            WHERE z.id = %s;
        """
        cur.execute(query, (application_id,))
        application = cur.fetchone()
        
        if not application:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
            
        return application
    finally:
        if conn: conn.close()

@app.put("/applications/{application_id}", response_model=ApplicationOut, tags=["Applications"])
async def update_application(
    application_id: int,
    application_update: ApplicationUpdate,
    x_anonymous_user_id: Annotated[int, Header()],
    _: bool = Depends(verify_user_session)
):
    """Обновляет заявку. Только анонимный создатель может ее обновить."""
    conn = None
    try:
        conn = get_main_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT id_заказчика FROM main.заявки WHERE id = %s;", (application_id,))
        owner = cur.fetchone()
        if not owner:
            raise HTTPException(status_code=404, detail="Заявка не найдена")
        if owner['id_заказчика'] != x_anonymous_user_id:
            raise HTTPException(status_code=403, detail="У вас нет прав на редактирование этой заявки")
        
        update_data = application_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="Нет данных для обновления")
        
        set_query_parts = [f'"{key}" = %s' for key in update_data.keys()]
        query = f"UPDATE main.заявки SET {', '.join(set_query_parts)}, дата_изменения = NOW() WHERE id = %s RETURNING *;"
        
        cur.execute(query, (*update_data.values(), application_id))
        updated_app = cur.fetchone()

        # ИСПРАВЛЕНИЕ: Добавляем второй запрос, чтобы получить 'наименование_заказчика'
        if updated_app:
            cur.execute('SELECT "наименование_юр_лица" FROM main.юр_лица WHERE id = %s', (updated_app['id_заказчика'],))
            company_info = cur.fetchone()
            updated_app['наименование_заказчика'] = company_info['наименование_юр_лица'] if company_info else None
            
        conn.commit()
        return updated_app
    finally:
        if conn: conn.close()

@app.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Applications"])
async def delete_application(
    application_id: int,
    x_anonymous_user_id: Annotated[int, Header()],
    _: bool = Depends(verify_user_session)
):
    """Удаляет заявку. Только анонимный создатель может ее удалить."""
    conn = None
    try:
        conn = get_main_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id_заказчика FROM main.заявки WHERE id = %s;", (application_id,))
        owner = cur.fetchone()
        
        if owner and owner[0] == x_anonymous_user_id:
            cur.execute("DELETE FROM main.заявки WHERE id = %s;", (application_id,))
            conn.commit()
        elif owner and owner[0] != x_anonymous_user_id:
            raise HTTPException(status_code=403, detail="У вас нет прав на удаление этой заявки")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
