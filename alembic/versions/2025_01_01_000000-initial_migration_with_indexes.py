"""initial_migration_with_indexes

Revision ID: initial001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'initial001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migración inicial: Crea todas las tablas con índices optimizados.
    
    Esta migración asume que las tablas ya existen. Si es una base de datos nueva,
    las tablas se crearán. Si ya existen, solo se agregarán los índices faltantes.
    """
    # Crear tabla de usuarios (si no existe)
    op.execute("""
        CREATE TABLE IF NOT EXISTS "user" (
            id SERIAL PRIMARY KEY,
            email VARCHAR(320) NOT NULL UNIQUE,
            hashed_password VARCHAR(1024) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            first_name VARCHAR(255),
            last_name VARCHAR(255)
        );
    """)
    
    # Crear tabla de marcas (si no existe)
    op.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES "user"(id),
            mark_type VARCHAR(50) NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            address VARCHAR(500),
            po_number VARCHAR(100)
        );
    """)
    
    # Crear índices en la tabla marks
    # Índice simple en user_id
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_marks_user_id 
        ON marks(user_id);
    """)
    
    # Índice simple en timestamp
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_marks_timestamp 
        ON marks(timestamp);
    """)
    
    # Índice compuesto user_id + timestamp (para reportes por usuario)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_marks_user_timestamp 
        ON marks(user_id, timestamp);
    """)
    
    # Índice compuesto user_id + mark_type + timestamp (para filtros específicos)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_marks_user_type_timestamp 
        ON marks(user_id, mark_type, timestamp);
    """)
    
    print("✅ Tablas e índices creados correctamente")


def downgrade() -> None:
    """
    Revertir la migración: Eliminar índices y tablas.
    """
    # Eliminar índices
    op.execute("DROP INDEX IF EXISTS idx_marks_user_type_timestamp;")
    op.execute("DROP INDEX IF EXISTS idx_marks_user_timestamp;")
    op.execute("DROP INDEX IF EXISTS idx_marks_timestamp;")
    op.execute("DROP INDEX IF EXISTS idx_marks_user_id;")
    
    # Eliminar tablas
    op.execute("DROP TABLE IF EXISTS marks;")
    op.execute("DROP TABLE IF EXISTS \"user\";")
    
    print("✅ Tablas e índices eliminados correctamente")

