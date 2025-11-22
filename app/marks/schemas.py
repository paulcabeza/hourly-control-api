from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.marks.models import MarkType


class MarkCreate(BaseModel):
    """Schema para crear una nueva marca (clock in/out)"""
    mark_type: MarkType
    latitude: float = Field(..., ge=-90, le=90, description="Latitude between -90 and 90")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude between -180 and 180")
    po_number: Optional[str] = Field(None, max_length=100, description="Purchase Order number")


class MarkRead(BaseModel):
    """Schema para leer una marca"""
    id: int
    user_id: int
    mark_type: MarkType
    timestamp: datetime
    latitude: float
    longitude: float
    address: Optional[str] = None
    po_number: Optional[str] = None

    class Config:
        from_attributes = True


class MarkUpdate(BaseModel):
    """Schema para actualizar una marca existente"""
    timestamp: Optional[datetime] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude between -90 and 90")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude between -180 and 180")
    address: Optional[str] = None
    po_number: Optional[str] = Field(None, max_length=100, description="Purchase Order number")


class MarkCreateAdmin(BaseModel):
    """Schema para crear una marca manualmente (solo admin)"""
    user_id: int
    mark_type: MarkType
    timestamp: datetime
    latitude: float = Field(..., ge=-90, le=90, description="Latitude between -90 and 90")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude between -180 and 180")
    po_number: Optional[str] = Field(None, max_length=100, description="Purchase Order number")
    clock_in_id: Optional[int] = Field(None, description="Optional reference clock in for clock out creation")


class MarkWithUser(MarkRead):
    """Schema para marca con información del usuario"""
    user_email: str
    user_first_name: Optional[str] = None
    user_last_name: Optional[str] = None

    class Config:
        from_attributes = True


class EmployeeSummary(BaseModel):
    """Schema para el resumen de horas de un empleado"""
    user_id: int
    user_email: str
    user_name: str
    total_hours: float


class EmployeesSummaryReport(BaseModel):
    """Schema para el reporte sumario de todos los empleados"""
    start_date: str
    end_date: str
    employees: List[EmployeeSummary]
