from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.dependencies import get_env_vars
from app.users.routes import users_router, auth_router, admin_router
from app.marks.routes import router as marks_router
from app.db.postgres_connector import create_db_and_tables

env = get_env_vars()

app = FastAPI(
    title="Clock Hourly Report API",
    description="API for managing employee clock in/out records",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=env.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/auth/jwt", tags=["auth"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(admin_router)  # Ya tiene prefix="/admin"
app.include_router(marks_router)  # Rutas de marcas (clock in/out)

@app.on_event("startup")
async def on_startup():
    """Crear tablas al iniciar la aplicación"""
    await create_db_and_tables()

@app.get("/health")
async def health_check():
    return {"status_code": 200, "message": "OK"}