from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from app.core.dependencies import get_env_vars
import logging
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

env = get_env_vars()

# Base declarativa para modelos
class Base(DeclarativeBase):
    pass

def clean_postgres_url(url: str) -> str:
    """Limpia la URL de PostgreSQL para hacerla compatible con asyncpg."""
    parsed = urlparse(url)
    
    # Asegurarse que usa el driver asyncpg
    scheme = 'postgresql+asyncpg'
    
    # Reconstruir la URL sin parámetros problemáticos
    cleaned_url = f"{scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}"
    
    # Agregar puerto si existe
    if parsed.port:
        cleaned_url += f":{parsed.port}"
    
    # Agregar nombre de base de datos
    cleaned_url += f"/{parsed.path.lstrip('/')}"
    
    return cleaned_url

# Engine async para PostgreSQL
engine = create_async_engine(
    clean_postgres_url(env.POSTGRES_DATABASE_URL),
    poolclass=NullPool,  # Mejor para FastAPI/Uvicorn multiple workers
    echo=False  # True para ver SQL queries (desarrollo)
)

# Session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Dependency para FastAPI
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Función para crear tablas (desarrollo/tests)
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)