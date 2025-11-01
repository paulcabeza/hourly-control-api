import uuid
from fastapi import Depends, APIRouter
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import BearerTransport, AuthenticationBackend, JWTStrategy
from fastapi_users.db import SQLAlchemyUserDatabase
from app.users.models import User
from app.db.postgres_connector import get_async_session
from app.users.schemas import UserRead, UserCreate, UserUpdate
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_env_vars
from app.users.manager import get_user_manager, get_user_db, UserManager

env = get_env_vars()

# Bearer transport
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# JWT strategy
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=env.JWT_SECRET, lifetime_seconds=env.JWT_LIFETIME_SECONDS)

# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance usa get_user_manager
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Current user dependencies
get_current_user = fastapi_users.current_user()
get_current_active_user = fastapi_users.current_user(active=True)
get_current_superuser = fastapi_users.current_user(active=True, superuser=True)

# Routers
users_router = fastapi_users.get_users_router(UserRead, UserUpdate)
auth_router = fastapi_users.get_auth_router(auth_backend)

# Admin router para crear usuarios (protegido, solo superuser)
admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.post("/users", response_model=UserRead)
async def create_user(
    user_create: UserCreate,
    user_manager: UserManager = Depends(get_user_manager),
    _: User = Depends(get_current_superuser),  # Solo superusers pueden crear usuarios
):
    """Crear un nuevo usuario (solo admin)"""
    user = await user_manager.create(user_create)
    return user

@admin_router.get("/users", response_model=list[UserRead])
async def get_all_users(
    session: AsyncSession = Depends(get_async_session),
    _: User = Depends(get_current_superuser),  # Solo superusers pueden listar usuarios
):
    """Obtener lista de todos los usuarios (solo admin)"""
    from sqlalchemy import select
    result = await session.execute(select(User))
    users = result.scalars().all()
    return users