# Imagen base ligera con Python 3.12
FROM python:3.12-slim

# Python sin ficheros .pyc y con salida sin buffer (los logs se ven al momento)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

# 1) Dependencias primero: esta capa se cachea y no se reconstruye
#    mientras requirements.txt no cambie
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Código fuente
COPY src/ ./src/

# 3) Usuario sin privilegios: dueño del código y con permiso para ejecutarlo
RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app \
    && chmod -R u+rX /app
USER appuser

EXPOSE 8000

# Comprueba que la API responde
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/health')" || exit 1

# 4) Comando de inicio. Se usa sh -c para poder leer la variable PORT.
#    exec hace que uvicorn sea el PID 1 y reciba bien las señales (docker stop)
CMD ["sh", "-c", "exec uvicorn main:app --app-dir src --host 0.0.0.0 --port ${PORT}"]
