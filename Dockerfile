FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar los navegadores de Playwright (solo chromium para ahorrar espacio)
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

# Variables de entorno por defecto
ENV PORT=5000

# Exponer el puerto
EXPOSE $PORT

# Comando para iniciar gunicorn (el servidor web de producción para Flask)
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
