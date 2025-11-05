import asyncio
import sys
import os
import getpass

# Agregar raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres_connector import get_async_session
from app.users.routes import get_user_db
from fastapi_users.password import PasswordHelper

# Importar modelos para registrar mapeos en SQLAlchemy antes de usar la sesión
# (evita: InvalidRequestError: expression 'Mark' failed to locate a name 'Mark')
from app.users.models import User  # noqa: F401
from app.marks.models import Mark  # noqa: F401


async def create_superuser_interactive():
    print("\n=== Crear Superuser (interactivo) ===\n")

    # Solicitar datos
    while True:
        email = input("Email: ").strip()
        if "@" in email and "." in email:
            break
        print("Email inválido. Intenta de nuevo.")

    while True:
        pwd1 = getpass.getpass("Password: ")
        pwd2 = getpass.getpass("Confirmar password: ")
        if not pwd1:
            print("El password no puede estar vacío.")
            continue
        if pwd1 != pwd2:
            print("Los passwords no coinciden. Intenta de nuevo.")
            continue
        break

    first_name = input("Nombre (opcional): ").strip() or None
    last_name = input("Apellido (opcional): ").strip() or None

    print("\nResumen:")
    print(f"  Email: {email}")
    print(f"  Nombre: {first_name or '-'}")
    print(f"  Apellido: {last_name or '-'}")
    confirm = input("\n¿Confirmar creación? (y/N): ").strip().lower()
    if confirm != "y":
        print("Cancelado.")
        return

    password_helper = PasswordHelper()
    hashed_password = password_helper.hash(pwd1)

    user_dict = {
        "email": email,
        "hashed_password": hashed_password,
        "is_active": True,
        "is_superuser": True,
        "is_verified": True,
        "first_name": first_name,
        "last_name": last_name,
    }

    # Usar session + user_db (fastapi-users db adapter)
    async for session in get_async_session():
        async for user_db in get_user_db(session):
            # Verificar si ya existe por email
            existing = await user_db.get_by_email(email)
            if existing:
                print(f"\nYa existe un usuario con ese email: {email}")
                return

            try:
                user = await user_db.create(user_dict)
                print(f"\n✅ Superuser creado: {user.email}")
            except Exception as e:
                print(f"\n❌ Error creando superuser: {e}")
                print("Asegúrate de haber corrido las migraciones (alembic upgrade head) y que la DB esté accesible.")
            return


if __name__ == "__main__":
    asyncio.run(create_superuser_interactive())