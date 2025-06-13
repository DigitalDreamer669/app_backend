# login_app.py 
from fastapi import FastAPI, HTTPException, status, Depends, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import os
import psycopg2
import psycopg2.extras
from psycopg2.extras import Json
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List, Annotated
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from pydantic import BaseModel, EmailStr, Field
import logging
from fastapi.middleware.cors import CORSMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

app = FastAPI()

# Настройки CORS
origins = [
    "http://localhost:7600",
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "null"  
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_admin_sessions = {}

def get_db_connection():
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
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

ADMIN_USERNAME_ENV = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_ENV = os.getenv("ADMIN_PASSWORD")

# --- Pydantic Models ---
class UserCreate(BaseModel):
    username: str = Field(..., max_length=50)
    password: str
    email: EmailStr
    is_active: Optional[bool] = True
    type_of_user: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=50)
    password: Optional[str] = None 
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    type_of_user: Optional[str] = None
    
class UserAdminLogin(BaseModel):
    username: str
    password: str

class UserFullResponse(BaseModel):
    id: UUID
    username: str
    password: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
    type_of_user: Optional[str] = None
    last_updated_device_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class UserPublicResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
    type_of_user: Optional[str] = None
    last_updated_device_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AdminLoginResponse(BaseModel):
    message: str
    token: str
    token_type: str

# --- Логика аутентификации ---
def cleanup_expired_sessions():
    current_time = datetime.now()
    expired_tokens = [token for token, expiry in active_admin_sessions.items() if current_time > expiry]
    for token in expired_tokens:
        active_admin_sessions.pop(token, None)

async def verify_admin_session(authorization: Annotated[str, Header()]):
    cleanup_expired_sessions()
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer" or token not in active_admin_sessions or datetime.now() > active_admin_sessions[token]:
            raise HTTPException(status_code=401, detail="Неверный или просроченный токен администратора")
        return True
    except (ValueError, AttributeError):
        raise HTTPException(status_code=401, detail="Неверный формат заголовка Authorization")

# --- API Endpoints ---
@app.post("/admin/login", response_model=AdminLoginResponse, tags=["Admin Authentication"])
async def admin_login(admin_login: UserAdminLogin):
    if (admin_login.username == ADMIN_USERNAME_ENV and admin_login.password == ADMIN_PASSWORD_ENV):
        session_token = str(uuid4())
        expiration_time = datetime.now() + timedelta(minutes=30)
        active_admin_sessions[session_token] = expiration_time
        return AdminLoginResponse(message="Admin login successful", token=session_token, token_type="bearer")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

@app.post("/admin/logout", tags=["Admin Authentication"])
async def admin_logout(authorization: Annotated[str, Header()]):
    # ... (код без изменений) ...
    try:
        scheme, token = authorization.split()
        if scheme.lower() == "bearer" and token in active_admin_sessions:
            active_admin_sessions.pop(token, None)
            return {"message": "Admin logout successful"}
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")


@app.post("/admin/users", response_model=UserPublicResponse, status_code=status.HTTP_201_CREATED, tags=["Admin User Management"])
async def admin_create_user(user: UserCreate, _: bool = Depends(verify_admin_session)):
    # ... (код без изменений) ...
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        insert_query = """
        INSERT INTO "login_data"."login_data" (username, password, email, is_active, type_of_user)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, username, email, is_active, created_at, updated_at, type_of_user, last_updated_device_info;
        """
        cur.execute(
            insert_query,
            (user.username, user.password, user.email, user.is_active, user.type_of_user)
        )
        new_user = cur.fetchone()
        conn.commit()
        return new_user
    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Пользователь с таким логином или email уже существует")
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    finally:
        if conn: conn.close()


@app.get("/admin/users", response_model=List[UserFullResponse], tags=["Admin User Management"])
async def admin_get_all_users(_: bool = Depends(verify_admin_session)):
    # ... (код без изменений) ...
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute('SELECT * FROM "login_data"."login_data" ORDER BY created_at DESC;')
        users = cur.fetchall()
        return users
    finally:
        if conn: conn.close()


@app.get("/admin/users/{user_id}", response_model=UserFullResponse, tags=["Admin User Management"])
async def admin_get_user_by_id(user_id: UUID, _: bool = Depends(verify_admin_session)):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # --- ИСПРАВЛЕНО: Преобразование UUID в строку ---
        cur.execute('SELECT * FROM "login_data"."login_data" WHERE id = %s;', (str(user_id),))
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    finally:
        if conn: conn.close()
        
@app.put("/admin/users/{user_id}", response_model=UserPublicResponse, tags=["Admin User Management"])
async def admin_update_user(user_id: UUID, user_data: UserUpdate, _: bool = Depends(verify_admin_session)):
    update_data = user_data.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    set_clauses = [f'"{key}" = %s' for key in update_data.keys()]
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        query = f"""
            UPDATE "login_data"."login_data"
            SET {', '.join(set_clauses)}, updated_at = NOW()
            WHERE id = %s
            RETURNING id, username, email, is_active, created_at, updated_at, type_of_user, last_updated_device_info;
        """
        # --- ИСПРАВЛЕНО: Преобразование UUID в строку ---
        params = list(update_data.values()) + [str(user_id)]
        cur.execute(query, params)
        
        updated_user = cur.fetchone()
        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User to update not found")
            
        conn.commit()
        return updated_user
    except psycopg2.errors.UniqueViolation:
        if conn: conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already in use")
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")
    finally:
        if conn: conn.close()

@app.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Admin User Management"])
async def admin_delete_user(user_id: UUID, _: bool = Depends(verify_admin_session)):
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # --- ИСПРАВЛЕНО: Преобразование UUID в строку ---
        cur.execute('DELETE FROM "login_data"."login_data" WHERE id = %s;', (str(user_id),))
        if cur.rowcount == 0:
            logger.warning(f"Attempted to delete non-existent user with ID: {user_id}")
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn: conn.close()