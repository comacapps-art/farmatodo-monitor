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

# Comando para iniciar el servidor web sin usar Gunicorn (ahorro masivo de memoria)
CMD ["python", "app.py"]
