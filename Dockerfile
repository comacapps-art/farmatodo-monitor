FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# El navegador ya viene instalado en esta imagen oficial, 
# pero nos aseguramos de que Playwright sepa dónde está.
RUN playwright install chromium

COPY . .

# Variables de entorno por defecto
ENV PORT=5000

# Exponer el puerto
EXPOSE $PORT

# Comando para iniciar gunicorn (el servidor web de producción para Flask)
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 300
