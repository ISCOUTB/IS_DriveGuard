"""
Crea el primer administrador. Es idempotente: si el correo ya existe, no hace nada.

Uso (desde backend/, con DATABASE_URL apuntando a la base de datos):
    ADMIN_EMAIL=admin@ejemplo.com ADMIN_PASSWORD='ClaveSegura123' python -m app.scripts.seed_admin

En PowerShell:
    $env:ADMIN_EMAIL="admin@ejemplo.com"; $env:ADMIN_PASSWORD="ClaveSegura123"
    python -m app.scripts.seed_admin

Dentro de Docker:
    docker-compose exec -e ADMIN_EMAIL=... -e ADMIN_PASSWORD=... backend python -m app.scripts.seed_admin
"""
import os
import sys

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.usuario import RolEnum, Usuario
from app.schemas.usuario import UsuarioCreate
from app.services.usuario_service import crear_usuario


def main() -> int:
    correo = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    nombre = os.environ.get("ADMIN_NAME", "Administrador")
    if not correo or not password:
        print("Define ADMIN_EMAIL y ADMIN_PASSWORD en el entorno.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        if db.scalar(select(Usuario.id).where(Usuario.correo == correo)):
            print(f"El usuario {correo} ya existe. No se hizo nada.")
            return 0
        datos = UsuarioCreate(
            nombre_completo=nombre, correo=correo, password=password, rol=RolEnum.ADMIN
        )
        crear_usuario(db, datos)
        print(f"Administrador {correo} creado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())