from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.db.postgres_connector import Base
import enum


class MarkType(str, enum.Enum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"


class Mark(Base):
    __tablename__ = "marks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    mark_type: Mapped[MarkType] = mapped_column(SQLEnum(MarkType), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    po_number: Mapped[str] = mapped_column(String(100), nullable=True)  # Purchase Order number
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="marks")

