from typing import Optional, TYPE_CHECKING
from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer
from app.db.postgres_connector import Base

if TYPE_CHECKING:
    from app.marks.models import Mark


class User(SQLAlchemyBaseUserTable[int], Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(length=255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(length=255), nullable=True)
    
    # Relationship (lazy="noload" para evitar cargar todas las marcas automáticamente)
    # Usar joinedload() o selectinload() explícitamente cuando se necesiten las marcas
    marks: Mapped[list["Mark"]] = relationship("Mark", back_populates="user", lazy="noload")