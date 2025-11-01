from typing import Optional
from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from app.db.postgres_connector import Base


class User(SQLAlchemyBaseUserTable[int], Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(length=255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(length=255), nullable=True)