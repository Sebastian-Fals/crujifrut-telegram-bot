# Imagen base ligera de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para optimizar cache
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del bot
COPY bot.py .
COPY .env.example .

# Crear directorio para logs
RUN mkdir -p logs

# Exponer puerto para health checks
EXPOSE 8080

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1 \
    LOG_LEVEL=INFO \
    ENVIRONMENT=production \
    PORT=8080

# Comando de inicio
CMD ["python", "bot.py"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import telegram; print('OK')" || exit 1