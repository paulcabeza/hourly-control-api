# ⏰ Clock Hourly Report API

API backend para el sistema de control de horas de empleados de MElectric. Construido con FastAPI, PostgreSQL y SQLAlchemy.

---

## 🚀 Características

- ✅ Autenticación con JWT (fastapi-users)
- ✅ Clock in/out con geolocalización
- ✅ Reverse geocoding automático (en background)
- ✅ Reportes semanales por usuario
- ✅ Panel de administración
- ✅ Migraciones de base de datos con Alembic
- ✅ Connection pooling optimizado
- ✅ Índices de base de datos para alto rendimiento

---

## 📋 Requisitos

- Python 3.12+
- PostgreSQL 14+
- pip

---

## 🛠️ Instalación (Desarrollo)

### 1. Clonar el repositorio

```bash
git clone <repo-url>
cd clock-hourly-report-api
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crear archivo `.env`:

```env
# Database
POSTGRES_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname

# Security
SECRET_KEY=tu-secret-key-super-segura-aqui
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Email (opcional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-password
```

### 5. Aplicar migraciones

```bash
alembic upgrade head
```

### 6. Crear superusuario

```bash
python scripts/create_superuser.py
```

### 7. Iniciar servidor

```bash
uvicorn main:app --reload
```

La API estará disponible en: `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

---

## 📁 Estructura del Proyecto

```
clock-hourly-report-api/
├── alembic/                    # Migraciones de base de datos
│   ├── versions/              # Archivos de migración
│   ├── env.py                 # Configuración de Alembic
│   └── README.md              # Documentación de migraciones
├── app/
│   ├── core/                  # Configuración central
│   │   ├── dependencies.py    # Dependencias de FastAPI
│   │   ├── env_vars.py        # Variables de entorno
│   │   └── logging_config.py  # Configuración de logs
│   ├── db/                    # Base de datos
│   │   └── postgres_connector.py  # Conexión y pool
│   ├── marks/                 # Módulo de marcas (clock in/out)
│   │   ├── models.py          # Modelos SQLAlchemy
│   │   ├── routes.py          # Endpoints
│   │   └── schemas.py         # Pydantic schemas
│   └── users/                 # Módulo de usuarios
│       ├── models.py          # Modelo de usuario
│       ├── routes.py          # Endpoints de autenticación
│       ├── schemas.py         # Schemas de usuario
│       └── manager.py         # Gestión de usuarios
├── scripts/                   # Scripts útiles
│   ├── create_superuser.py    # Crear administrador
│   └── deploy.sh              # Script de deployment
├── main.py                    # Punto de entrada de la aplicación
├── alembic.ini                # Configuración de Alembic
├── requirements.txt           # Dependencias Python
├── OPTIMIZATIONS.md           # Documentación de optimizaciones
└── README.md                  # Este archivo
```

---

## 🗄️ Migraciones de Base de Datos

Este proyecto usa **Alembic** para manejar las migraciones de base de datos.

### Comandos Principales

```bash
# Aplicar todas las migraciones
alembic upgrade head

# Ver estado actual
alembic current

# Ver historial
alembic history --verbose

# Crear nueva migración
alembic revision --autogenerate -m "descripcion"

# Revertir última migración
alembic downgrade -1
```

**📖 Documentación completa**: Ver `alembic/README.md`

---

## 🚀 Deployment en Producción

### Opción 1: Script Automático

```bash
./scripts/deploy.sh
```

Este script:
1. Crea backup de la base de datos
2. Aplica migraciones
3. Actualiza dependencias
4. Verifica el estado

### Opción 2: Manual

```bash
# 1. Backup de la base de datos
pg_dump $POSTGRES_DATABASE_URL > backup.sql

# 2. Pull de cambios
git pull origin main

# 3. Activar entorno virtual
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Aplicar migraciones
alembic upgrade head

# 6. Reiniciar la aplicación
systemctl restart melectric-api  # o tu método de restart
```

### Opción 3: Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Aplicar migraciones y iniciar
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 📊 Optimizaciones de Rendimiento

Este proyecto incluye varias optimizaciones críticas:

1. **Connection Pooling**: Pool de 10-30 conexiones a PostgreSQL
2. **Geocoding en Background**: No bloquea las respuestas de clock in/out
3. **Lazy Loading Optimizado**: Solo carga datos cuando se necesitan
4. **Índices de Base de Datos**: Optimización de consultas frecuentes

**Resultado**: 5-10x más rápido que sin optimizaciones

**📖 Documentación completa**: Ver `OPTIMIZATIONS.md`

---

## 🔐 Seguridad

- ✅ Autenticación JWT
- ✅ Passwords hasheados con bcrypt
- ✅ CORS configurado
- ✅ Variables de entorno para secrets
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Rate limiting (recomendado agregar)

---

## 📝 API Endpoints

### Autenticación

- `POST /auth/jwt/login` - Login
- `POST /auth/jwt/logout` - Logout
- `GET /users/me` - Usuario actual

### Marcas (Clock In/Out)

- `POST /marks/clock-in` - Marcar entrada
- `POST /marks/clock-out` - Marcar salida
- `GET /marks/my-marks` - Mis marcas
- `GET /marks/weekly-report` - Reporte semanal

### Admin

- `GET /admin/users` - Lista de usuarios
- `GET /admin/users/{id}` - Detalle de usuario
- `GET /admin/users/{id}/marks` - Marcas de usuario
- `PATCH /admin/users/{id}` - Actualizar usuario

**📖 Documentación interactiva**: `http://localhost:8000/docs`

---

## 🧪 Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-asyncio httpx

# Ejecutar tests
pytest

# Con cobertura
pytest --cov=app tests/
```

---

## 📈 Monitoreo

### Logs

Los logs se configuran en `app/core/logging_config.py`

```bash
# Ver logs en producción
tail -f /var/log/melectric-api/app.log

# O si usas systemd
journalctl -u melectric-api -f
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## 🛠️ Troubleshooting

### Error: "Can't connect to database"

```bash
# Verificar que PostgreSQL esté corriendo
pg_isready -h localhost -p 5432

# Verificar conexión
psql $POSTGRES_DATABASE_URL -c "SELECT 1"
```

### Error: "Alembic can't locate revision"

```bash
# Marcar la base de datos como inicializada
alembic stamp head
```

### Error: "Import error" al iniciar

```bash
# Verificar que el entorno virtual esté activado
which python  # Debe apuntar a venv/bin/python

# Reinstalar dependencias
pip install -r requirements.txt
```

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📄 Licencia

Este proyecto es privado y propiedad de MElectric.

---

## 👥 Autores

- **Paul Cabeza** - Desarrollo inicial

---

## 📞 Soporte

Para soporte o preguntas, contacta a: [tu-email@ejemplo.com]

---

## 🎯 Roadmap

- [ ] Rate limiting
- [ ] Webhooks para notificaciones
- [ ] Exportar reportes a PDF/Excel
- [ ] Integración con sistemas de nómina
- [ ] App móvil nativa
- [ ] Reconocimiento facial para clock in/out

---

## 🙏 Agradecimientos

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [fastapi-users](https://fastapi-users.github.io/fastapi-users/)

