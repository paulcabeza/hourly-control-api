import asyncio
import sys
import os
from typing import Dict, Any

# Añade el directorio raíz al path para importar módulos de la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.users.schemas import UserCreate
from app.db.postgres_connector import get_async_session, create_db_and_tables
from app.users.routes import get_user_db
from fastapi_users.password import PasswordHelper


async def create_superuser():
    # Primero, asegurarse que las tablas existen
    await create_db_and_tables()
    
    # Crear datos del usuario
    password_helper = PasswordHelper()
    password_hash = password_helper.hash("admin123")  # Quitamos el await
    
    user_dict = {
        "email": "admin@example.com",
        "hashed_password": password_hash,
        "is_active": True,
        "is_superuser": True,
        "is_verified": True,
        "first_name": "Admin",
        "last_name": "User"
    }
    
    # Obtener una sesión de DB
    async for session in get_async_session():
        async for user_db in get_user_db(session):
            try:
                user = await user_db.create(user_dict)
                print(f"Superuser created successfully: {user.email}")
                return user
            except Exception as e:
                print(f"Error creating superuser: {e}")
                raise

if __name__ == "__main__":
    asyncio.run(create_superuser())