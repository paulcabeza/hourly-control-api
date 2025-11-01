from fastapi_users import BaseUserManager
from app.users.models import User
from app.db.postgres_connector import get_async_session
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.dependencies import get_env_vars

env = get_env_vars()
SECRET = env.JWT_SECRET

class UserManager(BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    @staticmethod
    def parse_id(user_id: str) -> int:
        return int(user_id)

async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)
