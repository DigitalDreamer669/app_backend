# app.py
from fastapi import FastAPI, HTTPException, status, Depends, Header
from typing import Annotated
from pydantic import BaseModel
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
import logging
import psycopg2
import psycopg2.extras
from uuid import UUID
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Header
from typing import Annotated
import httpx



# Load environment variables from .env file
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

if not SECRET_KEY:
    logger.critical("КРИТИЧЕСКАЯ ОШИБКА: Переменная окружения SECRET_KEY не установлена!")

app = FastAPI()


# --- Модели Pydantic ---
# Модель для данных, которые мы извлекаем из токена
class TokenData(BaseModel):
    username: str
    user_id: str

# Модель для данных из вашей БД (как в прошлом примере)
class Product(BaseModel):
    id: UUID
    name: str
    price: float
    created_at: datetime


# --- ЗАВИСИМОСТЬ ДЛЯ ПРОВЕРКИ ТОКЕНА ---
async def get_current_user(authorization: Annotated[str, Header()]):
    """
    Проверяет заголовок Authorization, декодирует JWT и возвращает данные пользователя.
    Эта функция - "охранник" для наших эндпоинтов.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise credentials_exception

        # jwt.decode проверяет подпись и срок жизни токена. Если что-то не так, выдаст ошибку.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")

        if username is None or user_id is None:
            raise credentials_exception
        
        return TokenData(username=username, user_id=user_id)
    except (JWTError, ValueError):
        # Если токен невалиден (плохая подпись, истек срок, неверный формат)
        raise credentials_exception

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
    

# --- ДОБАВЬТЕ ЭТОТ ЗАЩИЩЕННЫЙ ЭНДПОИНТ ---
@app.get("/products/{product_id}", response_model=Product)
async def get_product_by_id(
    product_id: UUID,
    # Эта зависимость - наш "охранник". Если токен невалиден, до выполнения кода ниже дело не дойдет.
    current_user: Annotated[TokenData, Depends(get_current_user)]
):
    """
    Получает данные о продукте. Доступен только аутентифицированным пользователям.
    """
    logger.info(f"Пользователь '{current_user.username}' запрашивает продукт {product_id}")

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM main.products WHERE id = %s;", (str(product_id),))
        product_data = cur.fetchone()

        if not product_data:
            raise HTTPException(status_code=404, detail="Продукт не найден")
        
        return product_data
    finally:
        if conn:
            conn.close()

@app.get("/")
def root():
    return {"message": "Это сервис данных."}


