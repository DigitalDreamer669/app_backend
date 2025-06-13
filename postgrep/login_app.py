# app.py
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
from pydantic import BaseModel, EmailStr, validator
import logging
from fastapi.middleware.cors import CORSMiddleware
 

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

app = FastAPI()


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
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)


# --- Environment Variables Validation ---
required_env_vars = [
    "ADMIN_USERNAME", "ADMIN_PASSWORD",
    "DB_HOST_login", "DB_NAME_login", "DB_USER_login", "DB_PASSWORD_login"
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise RuntimeError(f"Missing required environment variables: {missing_vars}")

# --- Database Connection ---
def get_db_connection():
    try:
        db_host = os.getenv("DB_HOST_login")
        db_name = os.getenv("DB_NAME_login")
        db_user = os.getenv("DB_USER_login")
        db_password = os.getenv("DB_PASSWORD_login")

        conn = psycopg2.connect(
            host=db_host,
            port=5432,
            database=db_name,
            user=db_user,
            password=db_password
        )
        logger.info("Successfully connected to database")
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

# --- Admin Credentials ---
ADMIN_USERNAME_ENV = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_ENV = os.getenv("ADMIN_PASSWORD")

# In-memory session storage with expiration (use Redis in production)
active_admin_sessions = {}  # token: expiration_time

# --- Pydantic Models ---
class UserCreateUpdate(BaseModel):
    """
    Модель для создания нового пользователя или обновления его данных.
    """
    username: str
    password: str
    email: EmailStr
    is_active: Optional[bool] = True
    last_updated_device_info: Optional[Dict[str, Any]] = None

    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('Username must be between 3 and 50 characters')
        return v

    @validator('password')  
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    

class UserAdminLogin(BaseModel):
    """
    Модель для запроса входа администратора.
    """
    username: str
    password: str

class UserFullResponse(BaseModel):
    """
    Модель для полной информации о пользователе (для администратора).
    """
    id: UUID
    username: str
    password: str  # Пароль в открытом виде
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_updated_device_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class UserPublicResponse(BaseModel):
    """
    Модель для публичной информации о пользователе (без пароля).
    """
    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_updated_device_info: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class AdminLoginResponse(BaseModel):
    """
    Ответ на успешный вход администратора.
    """
    message: str
    token: str
    token_type: str

# --- Admin Authentication ---
def cleanup_expired_sessions():
    """Удаление истекших токенов"""
    current_time = datetime.now()
    expired_tokens = [token for token, expiry in active_admin_sessions.items() if current_time > expiry]
    for token in expired_tokens:
        active_admin_sessions.pop(token, None)

async def verify_admin_session(authorization: Annotated[str, Header()]):
    """
    Проверяет токен администратора из заголовка Authorization.
    Ожидаемый формат: "Bearer <token>"
    """
    cleanup_expired_sessions()  # Очищаем истекшие токены
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme. Use 'Bearer <token>'"
            )
        
        if token not in active_admin_sessions:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired admin session"
            )
        
        # Проверяем, не истек ли токен
        if datetime.now() > active_admin_sessions[token]:
            active_admin_sessions.pop(token, None)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin session expired"
            )
        
        return True
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'"
        )

# --- API Endpoints ---

@app.get("/")
async def root():
    """Корневой эндпоинт API."""
    return {
        "message": "Welcome to the User Management API!",
        "version": "1.0.0",
        "endpoints": {
            "admin_login": "POST /admin/login",
            "admin_users": "GET /admin/users",
            "admin_create_user": "POST /admin/users",
            "admin_get_user": "GET /admin/users/{user_id}",
            "admin_update_user": "PUT /admin/users/{user_id}",
            "admin_delete_user": "DELETE /admin/users/{user_id}"
        }
    }

@app.get("/health")
async def health_check():
    """Проверка состояния API."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}



# --- Admin Login Endpoint ---
@app.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(admin_login: UserAdminLogin):
    """
    Аутентификация администратора.
    """
    if (admin_login.username == ADMIN_USERNAME_ENV and 
        admin_login.password == ADMIN_PASSWORD_ENV):
        
        session_token = str(uuid4())
        # Токен истекает через 30 минут
        expiration_time = datetime.now() + timedelta(minutes=30)
        active_admin_sessions[session_token] = expiration_time
        
        logger.info(f"Successful admin login: {admin_login.username}")
        return AdminLoginResponse(
            message="Admin login successful",
            token=session_token,
            token_type="bearer"
        )
    
    logger.warning(f"Failed admin login attempt: {admin_login.username}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin credentials"
    )

@app.post("/admin/logout")
async def admin_logout(authorization: Annotated[str, Header()]):
    """
    Выход администратора из системы.
    """
    try:
        scheme, token = authorization.split()
        if scheme.lower() == "bearer" and token in active_admin_sessions:
            active_admin_sessions.pop(token, None)
            return {"message": "Admin logout successful"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

# --- Admin User Management Endpoints ---

@app.post("/admin/users", response_model=UserPublicResponse, status_code=status.HTTP_201_CREATED)
async def admin_create_user(user: UserCreateUpdate, _: bool = Depends(verify_admin_session)):
    """
    (Только для админов) Создание нового пользователя.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Проверяем существование пользователя
        cur.execute(
            """
            SELECT id FROM "login_data"."login_data"
            WHERE username = %s OR email = %s;
            """,
            (user.username, user.email)
        )
        existing_user = cur.fetchone()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this username or email already exists"
            )

        # Создаем пользователя
        insert_query = """
        INSERT INTO "login_data"."login_data" (
            username, password, email, is_active, last_updated_device_info
        ) VALUES (
            %s, %s, %s, %s, %s
        ) RETURNING id, username, email, is_active, created_at, updated_at, last_updated_device_info;
        """
        cur.execute(
            insert_query,
            (
                user.username,
                user.password,  # Пароль без шифрования
                user.email,
                user.is_active,
                Json(user.last_updated_device_info) if user.last_updated_device_info else None
            )
        )
        new_user = cur.fetchone()
        conn.commit()

        if not new_user:
            raise HTTPException(status_code=500, detail="Failed to create user")

        logger.info(f"Admin created new user: {user.username}")
        return UserPublicResponse(**new_user)

    except HTTPException as e:
        if conn:
            conn.rollback()
        raise e
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/admin/users", response_model=List[UserFullResponse])
async def admin_get_all_users(_: bool = Depends(verify_admin_session)):
    """
    (Только для админов) Получение списка всех пользователей с паролями.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT id, username, password, email, is_active, created_at, updated_at, last_updated_device_info
            FROM "login_data"."login_data"
            ORDER BY created_at DESC;
            """
        )
        users = cur.fetchall()

        logger.info("Admin retrieved all users list")
        return users
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.get("/admin/users/{user_id}", response_model=UserFullResponse)
async def admin_get_user_by_id(user_id: UUID, _: bool = Depends(verify_admin_session)):
    """
    (Только для админов) Получение пользователя по ID с паролем.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """
            SELECT id, username, password, email, is_active, created_at, updated_at, last_updated_device_info
            FROM "login_data"."login_data"
            WHERE id = %s;
            """,
            (str(user_id),)  # Преобразуем UUID в строку
        )
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        logger.info(f"Admin retrieved user: {user['username']}")
        return user
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.put("/admin/users/{user_id}", response_model=UserPublicResponse)
async def admin_update_user(user_id: UUID, user_data: UserCreateUpdate, _: bool = Depends(verify_admin_session)):
    """
    (Только для админов) Обновление данных пользователя.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Проверяем конфликты с другими пользователями
        cur.execute(
            """
            SELECT id FROM "login_data"."login_data"
            WHERE (username = %s OR email = %s) AND id != %s;
            """,
            (user_data.username, user_data.email, str(user_id))  # Преобразуем UUID в строку
        )
        conflict_user = cur.fetchone()
        if conflict_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username or email already exists for another user"
            )

        update_query = """
        UPDATE "login_data"."login_data"
        SET
            username = %s,
            password = %s,
            email = %s,
            is_active = %s,
            last_updated_device_info = %s,
            updated_at = NOW()
        WHERE
            id = %s
        RETURNING id, username, email, is_active, created_at, updated_at, last_updated_device_info;
        """
        cur.execute(
            update_query,
            (
                user_data.username,
                user_data.password,  # Пароль без шифрования
                user_data.email,
                user_data.is_active,
                Json(user_data.last_updated_device_info) if user_data.last_updated_device_info else None,
                str(user_id)  # Преобразуем UUID в строку
            )
        )
        updated_user = cur.fetchone()
        conn.commit()

        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        logger.info(f"Admin updated user: {user_data.username}")
        return UserPublicResponse(**updated_user)

    except HTTPException as e:
        if conn:
            conn.rollback()
        raise e
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            cur.close()
            conn.close()

@app.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_user(user_id: UUID, _: bool = Depends(verify_admin_session)):
    """
    (Только для админов) Удаление пользователя.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Сначала получаем информацию о пользователе для логирования
        cur.execute(
            "SELECT username FROM \"login_data\".\"login_data\" WHERE id = %s;",
            (str(user_id),)  # Преобразуем UUID в строку
        )
        user_info = cur.fetchone()
        
        if not user_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        cur.execute(
            """
            DELETE FROM "login_data"."login_data"
            WHERE id = %s;
            """,
            (str(user_id),)  # Преобразуем UUID в строку
        )
        conn.commit()
        
        if cur.rowcount == 0:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        logger.info(f"Admin deleted user: {user_info[0]}")
        
        return  # No content for 204
    except HTTPException as e:
        if conn:
            conn.rollback()
        raise e
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        if conn:
            cur.close()
            conn.close()

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)