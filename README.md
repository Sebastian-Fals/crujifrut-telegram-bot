# 🤖 Crujifrut Telegram Bot

Bot de Telegram para gestión de ventas y gastos del negocio Crujifrut con integración a Google Sheets.

## 🚀 Despliegue en Easypanel

### Prerrequisitos
- Repositorio en GitHub (privado)
- Token de Telegram válido
- Credenciales de Google Sheets API
- Servidor Contabo con Easypanel

### Paso 1: Configurar Repositorio

1. **Subir cambios a GitHub:**
```bash
git add .
git commit -m "Add Docker configuration for deployment"
git push origin main
```

### Paso 2: Configurar en Easypanel

1. **Crear Nuevo Servicio:**
   - Tipo: `Docker`
   - Source: `GitHub`
   - Repository URL: `https://github.com/tu-usuario/crujifrut-telegram-bot.git`
   - Branch: `main`

2. **Configurar Build:**
   - Build Method: `Dockerfile`
   - Dockerfile Path: `Dockerfile`

3. **Configurar Variables de Entorno:**
   ```
   TELEGRAM_TOKEN=7501575892:AAH0ZpxVk0hR-7Iq3bRFAh8iBvk0JWkFHyM
   SPREADSHEET_ID=1RqWOA0ZQGolq-e2zkqRDL0R_Lsnh4Qnz-oNv4GvXhNc
   CREDENTIALS_FILE=credentials.json
   PORT=8080
   LOG_LEVEL=INFO
   ENVIRONMENT=production
   ```

4. **Configurar Ports:**
   - Container Port: `8080`
   - Protocol: `TCP`

5. **Configurar Volumes (para credenciales):**
   - Host Path: `/path/to/your/credentials.json`
   - Container Path: `/app/credentials.json`
   - Type: `File`

### Paso 3: Deploy

1. Click en `Deploy`
2. Esperar a que termine el build
3. Verificar logs para confirmar que el bot está corriendo

## 📋 Comandos del Bot

### Ventas
- `/nuevaventa` - Registrar nueva venta
- `/totventas` - Ver total de ventas
- `/cliente <nombre>` - Ver historial de cliente

### Gastos
- `/nuevogasto` - Registrar nuevo gasto
- `/totgastos` - Ver total de gastos
- `/resumen_gastos` - Resumen por categoría

### Reportes
- `/balance` - Balance general (ventas - gastos)
- `/resumen` - Resumen completo

## 🔧 Configuración Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Ejecutar bot
python bot.py
```

## 📁 Estructura de Archivos

```
crujifrut-telegram-bot/
├── bot.py              # Código principal del bot
├── requirements.txt    # Dependencias de Python
├── Dockerfile          # Configuración Docker
├── .dockerignore       # Archivos ignorados por Docker
├── .env.example        # Plantilla de variables de entorno
├── credentials.json    # Credenciales Google Sheets (no subir a repo)
└── README.md          # Este archivo
```

## 🛡️ Seguridad

- Mantener el repositorio privado
- No incluir `credentials.json` en el repo
- Rotar tokens de Telegram regularmente
- Usar variables de entorno para credenciales