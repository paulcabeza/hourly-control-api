import asyncio
import sys
import os
import getpass

# Agregar raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.postgres_connector import get_async_session
from fastapi_users.password import PasswordHelper
from sqlalchemy import text


async def reset_password():
    print("\n=== Resetear Contraseña de Usuario ===\n")

    # Solicitar email
    email = input("Email del usuario: ").strip()
    if not email or "@" not in email:
        print("Email inválido.")
        return

    # Solicitar nueva contraseña
    while True:
        pwd1 = getpass.getpass("Nueva contraseña: ")
        pwd2 = getpass.getpass("Confirmar nueva contraseña: ")
        if not pwd1:
            print("La contraseña no puede estar vacía.")
            continue
        if pwd1 != pwd2:
            print("Las contraseñas no coinciden. Intenta de nuevo.")
            continue
        break

    # Hash password usando el mismo helper que fastapi-users
    password_helper = PasswordHelper()
    hashed_password = password_helper.hash(pwd1)

    # Actualizar en la base de datos
    async for session in get_async_session():
        try:
            # Verificar si el usuario existe
            result = await session.execute(
                text("SELECT id, email FROM \"user\" WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()
            
            if not user:
                print(f"\n❌ No se encontró un usuario con el email: {email}")
                return

            print(f"\nUsuario encontrado:")
            print(f"  ID: {user[0]}")
            print(f"  Email: {user[1]}")
            
            confirm = input("\n¿Confirmar cambio de contraseña? (y/N): ").strip().lower()
            if confirm != "y":
                print("Cancelado.")
                return

            # Actualizar contraseña
            await session.execute(
                text("""
                    UPDATE "user" 
                    SET hashed_password = :hashed_password 
                    WHERE email = :email
                """),
                {
                    "email": email,
                    "hashed_password": hashed_password,
                }
            )
            await session.commit()
            print(f"\n✅ Contraseña actualizada exitosamente para: {email}")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error actualizando contraseña: {e}")
        finally:
            await session.close()
            return


if __name__ == "__main__":
    asyncio.run(reset_password())

