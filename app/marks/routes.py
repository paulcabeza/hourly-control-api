from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from datetime import datetime, timedelta, date, timezone
from typing import List, Optional
from app.db.postgres_connector import get_async_session
from app.marks.models import Mark, MarkType
from app.marks.schemas import MarkCreate, MarkRead, MarkWithUser, MarkUpdate, MarkCreateAdmin
from app.users.models import User
from app.users.routes import get_current_user, get_current_superuser
import httpx
import asyncio
import logging

router = APIRouter(prefix="/marks", tags=["marks"])
logger = logging.getLogger(__name__)


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
        logger.warning(f"Error getting address: {e}")
    
    return f"Lat: {latitude:.6f}, Lon: {longitude:.6f}"


async def update_mark_address_background(mark_id: int, latitude: float, longitude: float):
    """
    Actualiza la dirección de una marca en background (no bloquea la respuesta)
    """
    try:
        # Obtener dirección desde coordenadas
        address = await get_address_from_coords(latitude, longitude)
        
        # Actualizar la marca en la base de datos
        async with get_async_session().__anext__() as session:
            result = await session.execute(
                select(Mark).where(Mark.id == mark_id)
            )
            mark = result.scalar_one_or_none()
            
            if mark:
                mark.address = address
                await session.commit()
                logger.info(f"Address updated for mark {mark_id}: {address}")
    except Exception as e:
        logger.error(f"Error updating address for mark {mark_id}: {e}")


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
    
    # Crear la marca con dirección temporal (coordenadas)
    # La dirección real se actualizará en background
    temp_address = f"Lat: {mark_data.latitude:.6f}, Lon: {mark_data.longitude:.6f}"
    
    new_mark = Mark(
        user_id=current_user.id,
        mark_type=MarkType.CLOCK_IN,
        timestamp=datetime.utcnow(),
        latitude=mark_data.latitude,
        longitude=mark_data.longitude,
        address=temp_address,
        po_number=mark_data.po_number
    )
    
    session.add(new_mark)
    await session.commit()
    await session.refresh(new_mark)
    
    # Actualizar dirección en background (no bloquea la respuesta)
    asyncio.create_task(
        update_mark_address_background(new_mark.id, mark_data.latitude, mark_data.longitude)
    )
    
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
    
    # Crear la marca con dirección temporal (coordenadas)
    # La dirección real se actualizará en background
    temp_address = f"Lat: {mark_data.latitude:.6f}, Lon: {mark_data.longitude:.6f}"
    
    new_mark = Mark(
        user_id=current_user.id,
        mark_type=MarkType.CLOCK_OUT,
        timestamp=datetime.utcnow(),
        latitude=mark_data.latitude,
        longitude=mark_data.longitude,
        address=temp_address,
        po_number=mark_data.po_number
    )
    
    session.add(new_mark)
    await session.commit()
    await session.refresh(new_mark)
    
    # Actualizar dirección en background (no bloquea la respuesta)
    asyncio.create_task(
        update_mark_address_background(new_mark.id, mark_data.latitude, mark_data.longitude)
    )
    
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
    
    # Agrupar y emparejar clock in/out permitiendo cruces de medianoche
    daily_sessions: dict[str, dict] = {}
    # Pila de sesiones abiertas (clock_in sin clock_out) durante el recorrido cronológico
    open_sessions_stack: list[tuple[str, dict]] = []  # (day_key_del_clock_in, session_ref)

    for mark in marks:
        # Calcular la llave del día para la vista (se agrupa por fecha del evento)
        day_key = mark.timestamp.date().isoformat()

        if day_key not in daily_sessions:
            daily_sessions[day_key] = {
                "date": day_key,
                "sessions": [],
                "total_hours": 0,
            }

        if mark.mark_type == MarkType.CLOCK_IN:
            # Crear la sesión y guardar referencia en la pila para un futuro CLOCK_OUT
            session_obj = {
                "clock_in": {
                    "id": mark.id,
                    "timestamp": mark.timestamp.isoformat(),
                    "address": mark.address,
                    "po_number": mark.po_number,
                    "latitude": mark.latitude,
                    "longitude": mark.longitude,
                },
                "clock_out": None,
                "hours_worked": 0,
            }
            daily_sessions[day_key]["sessions"].append(session_obj)
            open_sessions_stack.append((day_key, session_obj))
        elif mark.mark_type == MarkType.CLOCK_OUT:
            # Emparejar con el último clock_in abierto, aunque sea de otro día
            while open_sessions_stack:
                in_day_key, session_ref = open_sessions_stack.pop()
                if session_ref.get("clock_out") is None:
                    session_ref["clock_out"] = {
                        "id": mark.id,
                        "timestamp": mark.timestamp.isoformat(),
                        "address": mark.address,
                        "po_number": mark.po_number,
                        "latitude": mark.latitude,
                        "longitude": mark.longitude,
                    }

                    # Calcular horas trabajadas y sumar al día del clock_in
                    clock_in_time = datetime.fromisoformat(session_ref["clock_in"]["timestamp"])
                    clock_out_time = mark.timestamp
                    hours_worked = (clock_out_time - clock_in_time).total_seconds() / 3600
                    session_ref["hours_worked"] = round(hours_worked, 2)
                    daily_sessions[in_day_key]["total_hours"] += hours_worked
                    break
            # Si no hay clock_in abierto, ignoramos este clock_out "huérfano"
    
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


@router.put("/{mark_id}", response_model=MarkRead)
async def update_mark(
    mark_id: int,
    mark_update: MarkUpdate,
    _: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Actualizar una marca existente (solo admin).
    Permite actualizar timestamp, coordenadas, dirección y PO number.
    """
    # Obtener la marca
    result = await session.execute(
        select(Mark).where(Mark.id == mark_id)
    )
    mark = result.scalar_one_or_none()
    
    if not mark:
        raise HTTPException(status_code=404, detail="Mark not found")
    
    # Actualizar campos si se proporcionan
    if mark_update.timestamp is not None:
        # Guardar como NAIVE LOCAL: si viene con tz, quitar tz sin convertir
        timestamp = mark_update.timestamp
        if timestamp.tzinfo is not None:
            timestamp = timestamp.replace(tzinfo=None)
        mark.timestamp = timestamp
    if mark_update.latitude is not None:
        mark.latitude = mark_update.latitude
    if mark_update.longitude is not None:
        mark.longitude = mark_update.longitude
    if mark_update.address is not None:
        mark.address = mark_update.address
    if mark_update.po_number is not None:
        mark.po_number = mark_update.po_number
    
    # Si se actualizaron coordenadas pero no la dirección, actualizar la dirección
    if (mark_update.latitude is not None or mark_update.longitude is not None) and mark_update.address is None:
        asyncio.create_task(
            update_mark_address_background(mark.id, mark.latitude, mark.longitude)
        )
        # Usar dirección temporal mientras se actualiza
        mark.address = f"Lat: {mark.latitude:.6f}, Lon: {mark.longitude:.6f}"
    
    await session.commit()
    await session.refresh(mark)
    
    return mark


@router.post("/create", response_model=MarkRead)
async def create_mark_admin(
    mark_data: MarkCreateAdmin,
    _: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Crear una marca manualmente (solo admin).
    Útil para agregar clock out faltantes o corregir registros.
    """
    # Verificar que el usuario existe
    user_result = await session.execute(select(User).where(User.id == mark_data.user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Normalizar timestamp a UTC naive (best practice)
    timestamp = mark_data.timestamp
    if timestamp.tzinfo is not None:
        # Guardar como NAIVE LOCAL: quitar tz sin convertir
        timestamp = timestamp.replace(tzinfo=None)
    
    # Crear la marca con dirección temporal
    temp_address = f"Lat: {mark_data.latitude:.6f}, Lon: {mark_data.longitude:.6f}"
    
    new_mark = Mark(
        user_id=mark_data.user_id,
        mark_type=mark_data.mark_type,
        timestamp=timestamp,  # UTC naive
        latitude=mark_data.latitude,
        longitude=mark_data.longitude,
        address=temp_address,
        po_number=mark_data.po_number
    )
    
    session.add(new_mark)
    await session.commit()
    await session.refresh(new_mark)
    
    # Actualizar dirección en background
    asyncio.create_task(
        update_mark_address_background(new_mark.id, mark_data.latitude, mark_data.longitude)
    )
    
    return new_mark


@router.delete("/{mark_id}")
async def delete_mark(
    mark_id: int,
    _: User = Depends(get_current_superuser),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Eliminar una marca (solo admin).
    """
    result = await session.execute(
        select(Mark).where(Mark.id == mark_id)
    )
    mark = result.scalar_one_or_none()
    
    if not mark:
        raise HTTPException(status_code=404, detail="Mark not found")
    
    await session.delete(mark)
    await session.commit()
    
    return {"message": "Mark deleted successfully"}

