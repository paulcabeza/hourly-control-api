from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
from typing import List
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

