# 🗄️ Database Migrations con Alembic

Este directorio contiene todas las migraciones de base de datos del proyecto usando **Alembic**, el sistema estándar de migraciones para SQLAlchemy y FastAPI.

---

## 📁 Estructura

```
alembic/
├── versions/           # Archivos de migración (ordenados cronológicamente)
│   └── 2025_01_01_000000-initial_migration_with_indexes.py
├── env.py             # Configuración del entorno de Alembic
├── script.py.mako     # Template para nuevas migraciones
└── README.md          # Este archivo
```

---

## 🚀 Comandos Principales

### **1. Aplicar Migraciones (Desarrollo y Producción)**

```bash
# Aplicar todas las migraciones pendientes
alembic upgrade head

# Ver el estado actual
alembic current

# Ver historial de migraciones
alembic history --verbose
```

### **2. Crear Nueva Migración**

```bash
# Autogenerar migración basada en cambios en los modelos
alembic revision --autogenerate -m "descripcion_del_cambio"

# Crear migración vacía (manual)
alembic revision -m "descripcion_del_cambio"
```

### **3. Revertir Migraciones**

```bash
# Revertir la última migración
alembic downgrade -1

# Revertir a una migración específica
alembic downgrade <revision_id>

# Revertir todas las migraciones
alembic downgrade base
```

---

## 📋 Flujo de Trabajo

### **Desarrollo Local**

1. **Hacer cambios en los modelos** (`app/users/models.py`, `app/marks/models.py`)
2. **Crear migración automática**:
   ```bash
   alembic revision --autogenerate -m "agregar_campo_telefono"
   ```
3. **Revisar el archivo generado** en `alembic/versions/`
4. **Aplicar la migración**:
   ```bash
   alembic upgrade head
   ```
5. **Commit de la migración** al repositorio

### **Producción**

1. **Pull del código** con las nuevas migraciones
2. **Aplicar migraciones**:
   ```bash
   alembic upgrade head
   ```
3. **Reiniciar la aplicación** (si es necesario)

---

## 🎯 Ejemplos Comunes

### **Agregar un nuevo campo a una tabla**

1. Modificar el modelo:
```python
# app/users/models.py
class User(SQLAlchemyBaseUserTable[int], Base):
    # ... campos existentes ...
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
```

2. Crear migración:
```bash
alembic revision --autogenerate -m "add_phone_to_users"
```

3. Aplicar:
```bash
alembic upgrade head
```

### **Agregar un índice**

1. Modificar el modelo:
```python
# app/marks/models.py
class Mark(Base):
    # ... campos existentes ...
    
    __table_args__ = (
        Index('idx_marks_po_number', 'po_number'),  # Nuevo índice
        # ... otros índices ...
    )
```

2. Crear y aplicar migración (igual que arriba)

### **Crear una nueva tabla**

1. Crear el modelo en `app/<modulo>/models.py`
2. Importar en `alembic/env.py`:
```python
from app.<modulo>.models import NuevoModelo
```
3. Crear y aplicar migración

---

## ⚙️ Configuración

### **Variables de Entorno**

Alembic usa las mismas variables de entorno que la aplicación:

- `POSTGRES_DATABASE_URL`: URL de conexión a PostgreSQL

### **Archivo de Configuración**

- `alembic.ini`: Configuración principal
- `alembic/env.py`: Lógica de conexión y detección de modelos

---

## 🔍 Troubleshooting

### **Error: "Can't locate revision identified by 'head'"**

```bash
# Marcar la base de datos como inicializada
alembic stamp head
```

### **Error: "Target database is not up to date"**

```bash
# Aplicar migraciones pendientes
alembic upgrade head
```

### **Error: "Can't connect to database"**

Verificar que:
1. PostgreSQL esté corriendo
2. Las variables de entorno estén configuradas
3. La URL de conexión sea correcta

```bash
# Verificar conexión
psql $POSTGRES_DATABASE_URL -c "SELECT 1"
```

### **Migración genera cambios inesperados**

```bash
# Ver qué cambios detectó Alembic
alembic revision --autogenerate -m "test" --sql

# Si no quieres aplicarla, elimina el archivo generado
rm alembic/versions/<archivo>.py
```

---

## 📦 Despliegue en Producción

### **Opción 1: Manual (Recomendado para empezar)**

```bash
# SSH al servidor
ssh usuario@servidor

# Ir al directorio del proyecto
cd /path/to/project

# Activar entorno virtual
source venv/bin/activate

# Pull de cambios
git pull origin main

# Aplicar migraciones
alembic upgrade head

# Reiniciar la aplicación
systemctl restart melectric-api
```

### **Opción 2: Automático (CI/CD)**

Agregar a tu pipeline de deployment:

```yaml
# .github/workflows/deploy.yml
- name: Run Database Migrations
  run: |
    source venv/bin/activate
    alembic upgrade head
```

### **Opción 3: Docker**

```dockerfile
# Dockerfile
FROM python:3.12-slim

# ... instalación de dependencias ...

# Aplicar migraciones al iniciar
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

O usar un script de inicio:

```bash
# start.sh
#!/bin/bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🎓 Mejores Prácticas

### **1. Siempre revisar las migraciones autogeneradas**

Alembic puede no detectar todos los cambios correctamente. Revisa el archivo generado antes de aplicarlo.

### **2. Nunca editar migraciones ya aplicadas**

Si una migración ya se aplicó en producción, NO la edites. Crea una nueva migración para corregir.

### **3. Usar nombres descriptivos**

```bash
# ❌ Malo
alembic revision -m "cambios"

# ✅ Bueno
alembic revision -m "add_email_verification_to_users"
```

### **4. Probar migraciones localmente primero**

```bash
# Aplicar
alembic upgrade head

# Probar rollback
alembic downgrade -1

# Volver a aplicar
alembic upgrade head
```

### **5. Hacer backup antes de migrar en producción**

```bash
# Backup de PostgreSQL
pg_dump $POSTGRES_DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 📚 Recursos

- [Documentación oficial de Alembic](https://alembic.sqlalchemy.org/)
- [Tutorial de Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Autogenerate con Alembic](https://alembic.sqlalchemy.org/en/latest/autogenerate.html)

---

## 🆘 Soporte

Si tienes problemas con las migraciones:

1. Revisa los logs: `alembic history --verbose`
2. Verifica el estado: `alembic current`
3. Consulta este README
4. Revisa la documentación oficial de Alembic

