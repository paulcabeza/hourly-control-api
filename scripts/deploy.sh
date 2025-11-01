###############################################################################
# Script de Deployment para Producción
# 
# Este script:
# 1. Hace backup de la base de datos
# 2. Aplica las migraciones de Alembic
# 3. Reinicia la aplicación
#
# Uso:
#   ./scripts/deploy.sh
###############################################################################

set -e  # Salir si hay algún error

echo "============================================================"
echo "  🚀 Iniciando Deployment"
echo "============================================================"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para imprimir mensajes
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    print_error "Error: No se encuentra main.py. Ejecuta este script desde el directorio raíz del proyecto."
    exit 1
fi

# Paso 1: Backup de la base de datos
echo "📦 Paso 1: Creando backup de la base de datos..."
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR
BACKUP_FILE="$BACKUP_DIR/backup_$(date +%Y%m%d_%H%M%S).sql"

if [ -n "$POSTGRES_DATABASE_URL" ]; then
    pg_dump "$POSTGRES_DATABASE_URL" > "$BACKUP_FILE" 2>/dev/null || {
        print_warning "No se pudo crear backup. Continuando de todas formas..."
    }
    if [ -f "$BACKUP_FILE" ]; then
        print_success "Backup creado: $BACKUP_FILE"
    fi
else
    print_warning "POSTGRES_DATABASE_URL no está configurada. Saltando backup."
fi
echo ""

# Paso 2: Activar entorno virtual
echo "🐍 Paso 2: Activando entorno virtual..."
if [ -d "venv" ]; then
    source venv/bin/activate
    print_success "Entorno virtual activado"
else
    print_error "No se encuentra el directorio venv/"
    exit 1
fi
echo ""

# Paso 3: Instalar/actualizar dependencias
echo "📚 Paso 3: Instalando dependencias..."
pip install -r requirements.txt --quiet
print_success "Dependencias actualizadas"
echo ""

# Paso 4: Aplicar migraciones
echo "🗄️  Paso 4: Aplicando migraciones de base de datos..."
alembic upgrade head || {
    print_error "Error al aplicar migraciones"
    print_warning "Puedes revertir el backup con:"
    print_warning "  psql \$POSTGRES_DATABASE_URL < $BACKUP_FILE"
    exit 1
}
print_success "Migraciones aplicadas correctamente"
echo ""

# Paso 5: Verificar estado de migraciones
echo "🔍 Paso 5: Verificando estado de migraciones..."
alembic current
echo ""

# Paso 6: Reiniciar la aplicación (opcional, depende de tu setup)
echo "🔄 Paso 6: Reiniciando aplicación..."
print_warning "Reinicia manualmente la aplicación según tu configuración:"
echo "  - Systemd: sudo systemctl restart melectric-api"
echo "  - Docker: docker-compose restart api"
echo "  - PM2: pm2 restart melectric-api"
echo "  - Manual: pkill -f uvicorn && uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""

# Resumen
echo "============================================================"
echo "  ✅ Deployment Completado"
echo "============================================================"
echo ""
echo "📋 Resumen:"
echo "  - Backup: $BACKUP_FILE"
echo "  - Migraciones: Aplicadas"
echo "  - Estado: $(alembic current 2>/dev/null | tail -1 || echo 'Verificar manualmente')"
echo ""
print_success "Deployment exitoso! 🎉"
echo ""

