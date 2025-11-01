from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta, date
from typing import List, Optional
from app.db.postgres_connector import get_async_session
from app.marks.models import Mark, MarkType
from app.marks.schemas import MarkCreate, MarkRead, MarkWithUser
from app.users.models import User
from app.users.routes import get_current_user, get_current_superuser
import httpx

router = APIRouter(prefix="/marks", tags=["marks"])


async def get_address_from_coords(latitude: float, longitude: float) -> str:
    """
    Obtiene la dirección usando reverse geocoding de Nominatim (OpenStreetMap)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": latitude,
                    "lon": longitude,
                    "format": "json",
                },
                headers={"User-Agent": "MElectric-Hours-Control/1.0"},
                timeout=5.0
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("display_name", "Unknown location")
    except Exception as e:
        print(f"Error getting address: {e}")
    
    return f"Lat: {latitude:.6f}, Lon: {longitude:.6f}"


@router.post("/clock-in", response_model=MarkRead)
async def clock_in(
    mark_data: MarkCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Marcar entrada (clock in)"""
    # Verificar que el tipo sea clock_in
    if mark_data.mark_type != MarkType.CLOCK_IN:
        raise HTTPException(status_code=400, detail="Mark type must be 'clock_in'")
    
    # Obtener dirección desde coordenadas
    address = await get_address_from_coords(mark_data.latitude, mark_data.longitude)
    
    # Crear la marca
    new_mark = Mark(
        user_id=current_user.id,
        mark_type=MarkType.CLOCK_IN,
        timestamp=datetime.utcnow(),
        latitude=mark_data.latitude,
        longitude=mark_data.longitude,
        address=address,
        po_number=mark_data.po_number
    )
    
    session.add(new_mark)
    await session.commit()
    await session.refresh(new_mark)
    
    return new_mark


@router.post("/clock-out", response_model=MarkRead)
async def clock_out(
    mark_data: MarkCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Marcar salida (clock out)"""
    # Verificar que el tipo sea clock_out
    if mark_data.mark_type != MarkType.CLOCK_OUT:
        raise HTTPException(status_code=400, detail="Mark type must be 'clock_out'")
    
    # Obtener dirección desde coordenadas
    address = await get_address_from_coords(mark_data.latitude, mark_data.longitude)
    
    # Crear la marca
    new_mark = Mark(
        user_id=current_user.id,
        mark_type=MarkType.CLOCK_OUT,
        timestamp=datetime.utcnow(),
        latitude=mark_data.latitude,
        longitude=mark_data.longitude,
        address=address,
        po_number=mark_data.po_number
    )
    
    session.add(new_mark)
    await session.commit()
    await session.refresh(new_mark)
    
    return new_mark


@router.get("/my-marks", response_model=List[MarkRead])
async def get_my_marks(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    limit: int = 100
):
    """Obtener las marcas del usuario actual"""
    result = await session.execute(
        select(Mark)
        .where(Mark.user_id == current_user.id)
        .order_by(Mark.timestamp.desc())
        .limit(limit)
    )
    marks = result.scalars().all()
    return marks


@router.get("/all", response_model=List[MarkWithUser])
async def get_all_marks(
    _: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session),
    limit: int = 100
):
    """Obtener todas las marcas de todos los usuarios (solo admin)"""
    result = await session.execute(
        select(Mark, User)
        .join(User, Mark.user_id == User.id)
        .order_by(Mark.timestamp.desc())
        .limit(limit)
    )
    
    marks_with_users = []
    for mark, user in result.all():
        mark_dict = {
            "id": mark.id,
            "user_id": mark.user_id,
            "mark_type": mark.mark_type,
            "timestamp": mark.timestamp,
            "latitude": mark.latitude,
            "longitude": mark.longitude,
            "address": mark.address,
            "po_number": mark.po_number,
            "user_email": user.email,
            "user_first_name": user.first_name,
            "user_last_name": user.last_name,
        }
        marks_with_users.append(mark_dict)
    
    return marks_with_users


@router.get("/user/{user_id}", response_model=List[MarkRead])
async def get_user_marks(
    user_id: int,
    _: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session),
    limit: int = 100
):
    """Obtener las marcas de un usuario específico (solo admin)"""
    result = await session.execute(
        select(Mark)
        .where(Mark.user_id == user_id)
        .order_by(Mark.timestamp.desc())
        .limit(limit)
    )
    marks = result.scalars().all()
    return marks


@router.get("/weekly-report/{user_id}")
async def get_weekly_report(
    user_id: int,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    _: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Obtener reporte semanal de un usuario con horas trabajadas.
    Por defecto: sábado a viernes de la semana actual.
    """
    # Calcular fechas por defecto (sábado a viernes)
    if not start_date or not end_date:
        today = date.today()
        # Encontrar el sábado más reciente
        days_since_saturday = (today.weekday() + 2) % 7
        last_saturday = today - timedelta(days=days_since_saturday)
        next_friday = last_saturday + timedelta(days=6)
        
        start_date_obj = datetime.combine(last_saturday, datetime.min.time())
        end_date_obj = datetime.combine(next_friday, datetime.max.time())
    else:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    
    # Obtener usuario
    user_result = await session.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Obtener todas las marcas en el rango de fechas
    result = await session.execute(
        select(Mark)
        .where(
            and_(
                Mark.user_id == user_id,
                Mark.timestamp >= start_date_obj,
                Mark.timestamp <= end_date_obj
            )
        )
        .order_by(Mark.timestamp.asc())
    )
    marks = result.scalars().all()
    
    # Agrupar marcas por día y emparejar clock_in con clock_out
    daily_sessions = {}
    
    for mark in marks:
        day_key = mark.timestamp.date().isoformat()
        
        if day_key not in daily_sessions:
            daily_sessions[day_key] = {
                "date": day_key,
                "sessions": [],
                "total_hours": 0
            }
        
        if mark.mark_type == MarkType.CLOCK_IN:
            # Agregar nueva sesión con clock_in
            daily_sessions[day_key]["sessions"].append({
                "clock_in": {
                    "id": mark.id,
                    "timestamp": mark.timestamp.isoformat(),
                    "address": mark.address,
                    "po_number": mark.po_number,
                    "latitude": mark.latitude,
                    "longitude": mark.longitude
                },
                "clock_out": None,
                "hours_worked": 0
            })
        elif mark.mark_type == MarkType.CLOCK_OUT:
            # Buscar la última sesión sin clock_out
            sessions = daily_sessions[day_key]["sessions"]
            for session in reversed(sessions):
                if session["clock_out"] is None:
                    session["clock_out"] = {
                        "id": mark.id,
                        "timestamp": mark.timestamp.isoformat(),
                        "address": mark.address,
                        "po_number": mark.po_number,
                        "latitude": mark.latitude,
                        "longitude": mark.longitude
                    }
                    
                    # Calcular horas trabajadas
                    clock_in_time = datetime.fromisoformat(session["clock_in"]["timestamp"])
                    clock_out_time = mark.timestamp
                    hours_worked = (clock_out_time - clock_in_time).total_seconds() / 3600
                    session["hours_worked"] = round(hours_worked, 2)
                    daily_sessions[day_key]["total_hours"] += hours_worked
                    break
    
    # Calcular total de horas de la semana
    total_week_hours = sum(day["total_hours"] for day in daily_sessions.values())
    
    # Convertir a lista ordenada por fecha
    daily_list = sorted(daily_sessions.values(), key=lambda x: x["date"])
    
    return {
        "user_id": user_id,
        "user_email": user.email,
        "user_name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email,
        "start_date": start_date_obj.date().isoformat(),
        "end_date": end_date_obj.date().isoformat(),
        "daily_reports": daily_list,
        "total_hours": round(total_week_hours, 2)
    }

