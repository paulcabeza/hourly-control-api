from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
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

# Engine async para PostgreSQL con connection pooling optimizado
engine = create_async_engine(
    clean_postgres_url(env.POSTGRES_DATABASE_URL),
    pool_size=10,           # Mantener 10 conexiones abiertas permanentemente
    max_overflow=20,        # Hasta 20 conexiones adicionales bajo demanda
    pool_pre_ping=True,     # Verificar que la conexión esté viva antes de usar
    pool_recycle=3600,      # Reciclar conexiones cada hora (evita conexiones stale)
    echo=False              # True para ver SQL queries (desarrollo)
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